import streamlit as st

def load_css():
    """
    Loads compact CSS styles for the Streamlit application.
    Buttons are smaller, spacing is condensed, and layout is tighter.
    """
    st.markdown("""
    <style>
    :root {
        --primary-color: #3498db;
        --secondary-color: #28a745;
        --background-color: #f9f9f9;
        --card-background: #ffffff;
        --text-color: #2c3e50;
        --accent-color: #e74c3c;
    }

    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: var(--text-color);
        background-color: var(--background-color);
    }

    /* Remove excess padding */
    .main .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }

    /* Hide default header */
    .stApp > header { height: 0; }

    /* Compact headings */
    .main h1 {
        color: var(--text-color);
        border-bottom: 2px solid var(--primary-color);
        padding-bottom: 4px;
        margin: 0 0 10px 0 !important;
        font-size: 1.4rem;
        font-weight: bold;
    }

    /* Compact buttons */
    div.stButton > button {
        width: 100%;
        min-height: 32px;
        font-size: 0.9rem;
        font-weight: 600;
        border-radius: 6px;
        border: 2px solid var(--primary-color);
        padding: 4px 8px;
        margin: 4px 0;
    }

    div.stButton > button:hover {
        background-color: var(--primary-color);
        color: white;
        cursor: pointer;
    }

    /* Form submit button */
    .stFormSubmitButton > button {
        width: 100%;
        min-height: 32px;
        font-size: 0.9rem;
        font-weight: 600;
        border-radius: 6px;
        border: none;
        background: var(--primary-color);
        color: white;
        padding: 4px 8px;
        margin: 4px 0;
    }

    .stFormSubmitButton > button:hover {
        background: #2980b9;
    }

    /* Compact cards */
    .cart-container, .order-card {
        background-color: var(--card-background);
        border: 1px solid #ddd;
        border-radius: 6px;
        padding: 10px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* Compact table */
    .product-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 8px;
        font-size: 0.85rem;
    }

    .product-table th, .product-table td {
        padding: 6px;
        border: 1px solid #e9ecef;
    }

    /* Alerts */
    .stAlert > div {
        border-radius: 6px;
        padding: 8px;
        font-size: 0.9rem;
    }

    @media (max-width: 768px) {
        div.stButton > button, .stFormSubmitButton > button {
            font-size: 0.85rem;
            min-height: 28px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Make sidebar hidden and collapsed
def hide_sidebar():
    st.set_page_config(initial_sidebar_state="collapsed")
    # Completely hide the sidebar
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)