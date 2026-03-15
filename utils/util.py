import streamlit as st
import streamlit.components.v1 as components
import base64
import datetime
import socket

# # Format price from integer to dollar format
# def format_price(price_cents):
#     if price_cents is None:
#         return "$ 0.00"
#     return f"$ {abs(price_cents) / 100:.2f}"

def format_timestamp(timestamp_str):
    """Format timestamp for better display"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str
    
# # Calculate split amounts
# def calculate_split_amounts(total_amount, split_count):
#     if split_count <= 1:
#         return [total_amount]
    
#     base_amount = total_amount // split_count
#     remainder = total_amount % split_count
    
#     amounts = [base_amount] * split_count
    
#     # Distribute remainder starting from the last amounts
#     for i in range(remainder):
#         amounts[-(i+1)] += 1
    
#     return amounts

# Format price helper
def format_price(cents):
    return f"${cents / 100:.2f}"

# Calculate split amounts
def calculate_split_amounts(total, split_count):
    base_amount = total // split_count
    remainder = total % split_count
    
    amounts = [base_amount] * split_count
    for i in range(remainder):
        amounts[i] += 1
    
    return amounts

# Play background audio
def play_background_audio(file):
    with open(file, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        
    # HTML/JS to trigger playback without a visible player
    md = f"""
        <audio id="audio-tag" autoplay>
            <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
        </audio>
        <script>
            var audio = document.getElementById('audio-tag');
            audio.volume = 0.5; // Optional: Adjust volume
            audio.play();
        </script>
    """
    components.html(md, height=0, width=0)

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


# Printer IP and port
PRINTER_IP = "192.168.0.41"
PRINTER_PORT = 9100  # Standard raw printing port

def print_receipt(orders, subtotal, tax=45):
    try:
        # Connect to printer
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((PRINTER_IP, PRINTER_PORT))
        receipt_lines = []
        
        # Items
        for order_id, items in orders.items():
            for item in items:
                # Main product line
                receipt_lines.append(f"{item['description']}\n")
                receipt_lines.append(f"  Quantity: {item['quantity']}\n")
                receipt_lines.append(f"  Price: {format_price(item['base_price'])}\n")
                
                # Modifiers
                if item['modifiers']:
                    receipt_lines.append("  Modifiers:\n")
                    for mod in item['modifiers']:
                        receipt_lines.append(f"    - {mod['description']}: +{format_price(mod['price'])}\n")
                    receipt_lines.append(
                        f"  Item Price w/ Modifiers: {format_price(item['base_price'] + item['modifier_total'])}\n"
                    )
                
                receipt_lines.append(f"  Item Total: {format_price(item['item_total'])}\n")
                receipt_lines.append("-" * 50 + "\n")
            
            # Payment summary
            receipt_lines.append("\n")
            receipt_lines.append(f"Order ID: {'order_id'}%100 \n")
            receipt_lines.append(f"Subtotal: {format_price(subtotal)}\n")
            receipt_lines.append(f"Tax: {format_price(tax)}\n")
            receipt_lines.append("=" * 50 + "\n")
     
        # Convert to bytes
        receipt_data = "".join(receipt_lines).encode("utf-8")
        
        # Send receipt data
        sock.sendall(receipt_data)
        
        # Cut paper command (ESC/POS)
        sock.sendall(b"\x1dV\x00")    
        return True
    except Exception as e:
        st.error(f"Error saving receipt: {e}")
        return False