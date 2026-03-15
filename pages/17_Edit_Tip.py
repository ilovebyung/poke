import streamlit as st
import pandas as pd
import time
from utils.util import format_price
from utils.database import  get_db_connection 
from utils.style import load_css 

# Page configuration
st.set_page_config(page_title="Settle Transactions", page_icon="📒", layout="wide", initial_sidebar_state="collapsed")


# to be updated with data entry in the future
st.info("Data Entry Tips, Refund, and Manual adjustment  will be added here in the future.")