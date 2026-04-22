import streamlit as st
import qrcode
from PIL import Image
import random
import io
import time

def generate_upi_qr(amount):
    """Generates a dummy UPI QR code for simulation."""
    upi_url = f"upi://pay?pa=dummy@upi&pn=ExpenseTracker&am={amount}&cu=INR"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def show_payment_form(amount):
    """Displays payment simulation forms based on choice."""
    if 'payment_verified' not in st.session_state:
        st.session_state.payment_verified = False
        
    payment_mode = st.selectbox("Choose Payment Mode", ["UPI", "Netbanking", "Cards"])
    
    requires_otp = amount > 2000
    
    if payment_mode == "UPI":
        st.subheader("UPI Payment")
        upi_type = st.radio("Select UPI Method", ["Scan QR Code", "Enter UPI ID"])
        
        if upi_type == "Scan QR Code":
            qr_img = generate_upi_qr(amount)
            st.image(qr_img, caption=f"Total: ₹{amount}")
            st.info("Scan this QR with your UPI app.")
        else:
            st.text_input("Enter your UPI ID", placeholder="example@upi")
            st.info("You will receive a payment request on your UPI app.")
        
    elif payment_mode == "Netbanking":
        st.subheader("Netbanking Details")
        bank = st.selectbox("Select Bank", ["SBI", "HDFC", "ICICI", "Axis", "Kotak"])
        user_id = st.text_input("Customer ID")
        pwd = st.text_input("Password", type="password")
        
    elif payment_mode == "Cards":
        st.subheader("Card Details")
        st.text_input("Card Number", placeholder="XXXX XXXX XXXX XXXX")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Expiry (MM/YY)")
        with col2:
            st.text_input("CVV", type="password")
        st.text_input("Name on Card")

    if st.button("Confirm Payment"):
        if requires_otp:
            st.session_state.otp_sent = True
            st.session_state.correct_otp = str(random.randint(100000, 999999))
            st.warning(f"OTP Sent to linked mobile number (Simulated OTP: {st.session_state.correct_otp})")
        else:
            st.success("Payment Successful!")
            st.session_state.payment_verified = True
            st.rerun()

    if st.session_state.get('otp_sent'):
        otp_input = st.text_input("Enter 6-digit OTP")
        if st.button("Verify OTP"):
            if otp_input == st.session_state.correct_otp:
                st.success("OTP Verified!")
                st.session_state.payment_verified = True
                st.session_state.otp_sent = False
                st.rerun()
            else:
                st.error("Invalid OTP. Try again.")
    
    return st.session_state.payment_verified
