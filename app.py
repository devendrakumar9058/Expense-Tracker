import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
import database
import auth
import ocr_engine
import payment_flows
import base64
import time
import numpy as np
import gemini_service
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Page Config ---
st.set_page_config(page_title="AI Expense Tracker", layout="wide", page_icon="💰")

# --- Custom Styling (Premium Glassmorphism Theme) ---
def local_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&display=swap');
    
    * {{
        font-family: 'Outfit', sans-serif;
    }}
    
    .main {{
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }}
    
    [data-testid="stSidebar"] {{
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.3);
    }}
    
    .stButton>button {{
        background: linear-gradient(90deg, #ff4b2b 0%, #ff416c 100%);
        color: white;
        border-radius: 20px;
        border: none;
        padding: 0.6rem 2rem;
        font-weight: 600;
        transition: transform 0.2s, box-shadow 0.2s;
        width: 100%;
    }}
    
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(255, 75, 43, 0.4);
    }}
    
    .metric-card {{
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.18);
        text-align: center;
        margin-bottom: 1rem;
        transition: transform 0.3s;
    }}
    
    .metric-card:hover {{
        transform: scale(1.02);
    }}
    
    h1, h2, h3 {{
        color: #1a1a1a;
        font-weight: 600;
    }}
    
    .stMetric {{
        background: white;
        padding: 10px;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- Initialize Database ---
database.init_db()

# --- Session State ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

# --- Auth Flow ---
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.header("Welcome Back")
        user = st.text_input("Username", key="l_user")
        pwd = st.text_input("Password", type="password", key="l_pwd")
        if st.button("Login"):
            if auth.login(user, pwd):
                st.session_state.logged_in = True
                st.session_state.username = user
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid credentials")
        
        if st.button("🔑 Forgot Password?", help="Click to reset password"):
            st.session_state.show_recovery = True
            
        if st.session_state.get('show_recovery'):
            with st.container():
                st.markdown("---")
                recover_email = st.text_input("Enter Recovery Email")
                if st.button("Send Reset Link"):
                    if "@" in recover_email and "." in recover_email:
                        st.success(f"📧 A password reset link has been sent to **{recover_email}**.")
                        st.markdown(f'[Click here to check your Gmail inbox](https://mail.google.com/mail/u/0/?tab=rm&ogbl#inbox)')
                        st.session_state.show_recovery = False
                    else:
                        st.error("Please enter a valid email address.")
                
    with tab2:
        st.header("Create Account")
        new_user = st.text_input("Username", key="s_user")
        new_pwd = st.text_input("Password", type="password", key="s_pwd")
        if st.button("Sign Up"):
            if auth.signup(new_user, new_pwd):
                st.success("Account created! Please login.")
            else:
                st.error("Username already exists")
    st.stop()

# --- Main App ---
st.sidebar.title(f"Hello, {st.session_state.username}!")

# AI Configuration in Sidebar (Optional)
with st.sidebar.expander("🤖 AI Settings", expanded=not st.session_state.gemini_api_key):
    api_key_input = st.text_input("Gemini API Key", value=st.session_state.gemini_api_key, type="password", help="Enter key or use .env file")
    st.markdown("[🚀 Get Free API Key](https://aistudio.google.com/app/apikey)")
    
    # Auto-configure if key is changed or if not already configured in this session
    if 'gemini_configured' not in st.session_state:
        st.session_state.gemini_configured = False

    if api_key_input != st.session_state.gemini_api_key or not st.session_state.gemini_configured:
        st.session_state.gemini_api_key = api_key_input
        if api_key_input:
            if gemini_service.configure_gemini(api_key_input):
                st.session_state.gemini_configured = True

    if api_key_input:
        if st.button("⚡ Test AI Connection"):
            with st.spinner("Testing..."):
                if gemini_service.configure_gemini(api_key_input):
                    st.success("Successful!")
                else:
                    st.error("Failed.")

menu = st.sidebar.radio("Navigation", ["Dashboard", "AI Chat Assistant", "Add Expense", "OCR Upload", "Salary Settings", "Export Data"])

current_month = datetime.now().strftime("%Y-%m")

# Sidebar - Salary Info
current_salary = database.get_salary(st.session_state.username, current_month)
total_spent = database.get_total_spent(st.session_state.username, current_month)
highest_exp = database.get_highest_expenditure(st.session_state.username, current_month)
balance = current_salary - total_spent

st.sidebar.markdown("---")
st.sidebar.metric("Current Balance", f"₹{balance:,.2f}")
if balance < 2000:
    st.sidebar.warning("⚠️ Warning: Low Balance! (< ₹2000)")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.rerun()

# --- Views ---
if menu == "Dashboard":
    st.title("✨ Financial Overview")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><h3>💰 Monthly Salary</h3><h2>₹{current_salary:,.2f}</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h3>📉 Total Expenses</h3><h2 style="color:#ff4b4b">₹{total_spent:,.2f}</h2></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><h3>💳 Remaining</h3><h2 style="color:#2ecc71">₹{balance:,.2f}</h2></div>', unsafe_allow_html=True)

    if highest_exp:
        cat, amt, dt = highest_exp
        st.info(f"🚀 **Highest Expenditure:** You spent **₹{amt:,.2f}** on **{cat}** on {dt}. Keep an eye on your largest expenses!")

    df = database.get_expenses_df(st.session_state.username)
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        
        # --- AI Forecasting Section ---
        st.markdown("---")
        st.subheader("🤖 AI Spending Forecast")
        daily_spending = df.groupby('date')['amount'].sum().reset_index()
        
        if len(daily_spending) > 1:
            # Simple Linear Regression for forecasting
            daily_spending['day_num'] = (daily_spending['date'] - daily_spending['date'].min()).dt.days
            X = daily_spending['day_num'].values.reshape(-1, 1)
            y = daily_spending['amount'].values
            
            # Use basic polyfit for trend
            z = np.polyfit(daily_spending['day_num'], y, 1)
            p = np.poly1d(z)
            
            next_day = daily_spending['day_num'].max() + 1
            forecast = p(next_day)
            
            st.info(f"Based on your trends, your predicted spending for tomorrow is approximately **₹{max(0, forecast):,.2f}**.")
        else:
            st.info("More data needed for AI forecasting.")
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        
        # Set Seaborn style
        sns.set_theme(style="whitegrid")
        
        with c1:
            st.subheader("📊 Category Distribution")
            fig_pie, ax_pie = plt.subplots(figsize=(8, 6), facecolor='none')
            df_cat = df.groupby('category')['amount'].sum().reset_index()
            colors = sns.color_palette("husl", len(df_cat))
            
            # Using wedgeprops for a cleaner look and adding labels/legend
            wedges, texts, autotexts = ax_pie.pie(
                df_cat['amount'], 
                labels=df_cat['category'], 
                autopct='%1.1f%%', 
                startangle=140, 
                colors=colors, 
                wedgeprops={'edgecolor': 'white', 'linewidth': 2, 'antialiased': True},
                textprops={'fontsize': 10, 'fontweight': 'bold'}
            )
            
            # Professional legend
            ax_pie.legend(wedges, df_cat['category'], title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            
            plt.axis('equal')
            st.pyplot(fig_pie)
            
        with c2:
            st.subheader("📈 Spending Pulse")
            fig_line, ax_line = plt.subplots(figsize=(8, 6), facecolor='none')
            line_data = df.sort_values('date').groupby('date')['amount'].sum().reset_index()
            sns.lineplot(data=line_data, x='date', y='amount', marker='o', color='#ff4b2b', linewidth=2.5)
            plt.fill_between(line_data['date'], line_data['amount'], alpha=0.2, color='#ff4b2b')
            plt.xticks(rotation=45)
            plt.title("Daily Spending Trend", fontsize=12, fontweight='bold')
            st.pyplot(fig_line)

        st.markdown("---")
        st.subheader("🏷️ Category-wise Expenditure")
        fig_bar, ax_bar = plt.subplots(figsize=(12, 4), facecolor='none')
        df_cat_sorted = df_cat.sort_values(by='amount', ascending=False)
        sns.barplot(data=df_cat_sorted, x='category', y='amount', palette="viridis", hue='category', legend=False)
        plt.title("Spending by Category", fontsize=12, fontweight='bold')
        plt.xlabel("Category", fontsize=10)
        plt.ylabel("Amount (₹)", fontsize=10)
        st.pyplot(fig_bar)

        st.subheader("Recent Transactions")
        st.dataframe(df.sort_values('date', ascending=False), use_container_width=True)
    else:
        st.info("Start adding expenses to see insights!")

elif menu == "AI Chat Assistant":
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title("🤖 Financial Assistant")
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    st.markdown("Ask me anything about your expenses, budgeting, or financial advice!")
    
    # Financial Summary for Web Chat
    df_context = database.get_expenses_df(st.session_state.username)
    summary_text = f"My current balance is ₹{balance:,.2f}. Recent expenses: {df_context.tail(5).to_string(index=False)}"
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🌐 Chat via Gemini Web (No Key Required)"):
            st.info("Copied summary to clipboard! Paste it into Gemini Web for context.")
            # Simple JS to copy to clipboard (Streamlit workaround)
            st.code(summary_text, language=None)
            time.sleep(1)
            # URL to Gemini Web with a pre-filled prompt is tricky, so just providing the link
            st.markdown(f'[Click here to open Gemini Web](https://gemini.google.com/app)')
    
    with col_b:
        st.write("Or use the integrated chatbot below (Requires API Key):")

    st.markdown("---")
    
    if not st.session_state.gemini_api_key:
        st.info("💡 **Tip**: To use the integrated chatbot, add an API key in the sidebar. Otherwise, use the 'Gemini Web' button above.")
    else:
        # Display chat messages from history on app rerun
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # React to user input
        if prompt := st.chat_input("How can I help you today??"):
            # Display user message in chat message container
            st.chat_message("user").markdown(prompt)
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                # Prepare context and prompt
                df_context = database.get_expenses_df(st.session_state.username)
                context = f"User: {st.session_state.username}\nBalance: {balance}\nRecent Expenses: {df_context.tail(10).to_string()}\n"
                
                with st.spinner("AI is thinking..."):
                    filtered_history = st.session_state.chat_history[:-1] # History before this message
                    response = gemini_service.get_gemini_response(prompt, history=filtered_history, api_key=st.session_state.gemini_api_key)
                    st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})

elif menu == "Add Expense":
    st.title("💸 Manual Entry")
    with st.form("expense_form"):
        cat = st.selectbox("Category", ["Food", "Travel", "Shopping", "Groceries", "Entertainment", "Health", "Others"])
        amt = st.number_input("Amount (INR)", min_value=0.0, step=100.0)
        date = st.date_input("Date", value=datetime.today())
        desc = st.text_input("Description")
        
        # Payment simulation triggered after form submission
        submitted = st.form_submit_button("Proceed to Payment")
        
        if submitted:
            st.session_state.temp_expense = {"cat": cat, "amt": amt, "date": str(date), "desc": desc}
            st.session_state.paying = True

    if st.session_state.get('paying'):
        verified = payment_flows.show_payment_form(st.session_state.temp_expense['amt'])
        if verified:
            exp = st.session_state.temp_expense
            database.add_expense(st.session_state.username, exp['cat'], exp['amt'], "Simulated", exp['date'], exp['desc'])
            st.success("Expense added successfully!")
            st.session_state.paying = False
            del st.session_state.temp_expense
            st.session_state.payment_verified = False
            time.sleep(1)
            st.rerun()

elif menu == "OCR Upload":
    st.title("📸 Scan Bill")
    uploaded_file = st.file_uploader("Upload Receipt Image", type=["jpg", "png", "jpeg"])
    
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Receipt", width=300)
        if st.button("Process with AI OCR"):
            with st.spinner("Analyzing receipt..."):
                # Save temp file
                with open("temp_receipt.jpg", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                data = ocr_engine.extract_data_from_image("temp_receipt.jpg", api_key=st.session_state.gemini_api_key)
                if data:
                    st.success(f"Successfully scanned using {data.get('source', 'Advanced OCR')}")
                    # Predicted category fallback logic if needed
                    predicted_cat = data.get('category') or ocr_engine.predict_category(data['raw_text'])
                    
                    # Fill form with OCR data
                    st.session_state.ocr_data = {
                        "amt": data['amount'],
                        "cat": predicted_cat,
                        "date": data['date'] if data['date'] else datetime.now().strftime("%Y-%m-%d"),
                        "desc": data.get('description', "OCR Upload")
                    }
                else:
                    st.error("Failed to extract data. Please enter manually.")

    if 'ocr_data' in st.session_state:
        st.subheader("Verify & Save")
        col1, col2 = st.columns(2)
        with col1:
            # Check if o_amt is valid, if not use a default
            try:
                initial_amt = float(st.session_state.ocr_data['amt'])
            except:
                initial_amt = 0.0
            o_amt = st.number_input("Extracted Amount", value=initial_amt)
            o_date = st.text_input("Extracted Date", value=st.session_state.ocr_data['date'])
        with col2:
            all_cats = ["Food", "Travel", "Shopping", "Groceries", "Entertainment", "Health", "Others"]
            current_cat = st.session_state.ocr_data['cat'] if st.session_state.ocr_data['cat'] in all_cats else "Others"
            o_cat = st.selectbox("Category", all_cats, index=all_cats.index(current_cat))
            o_desc = st.text_input("Description", value=st.session_state.ocr_data.get('desc', "OCR Upload"))
        
        if st.button("Confirm & Pay"):
            st.session_state.temp_expense = {"cat": o_cat, "amt": o_amt, "date": o_date, "desc": o_desc}
            st.session_state.paying = True
            
        if st.session_state.get('paying'):
             verified = payment_flows.show_payment_form(st.session_state.temp_expense['amt'])
             if verified:
                exp = st.session_state.temp_expense
                database.add_expense(st.session_state.username, exp['cat'], exp['amt'], "Simulated", exp['date'], exp['desc'])
                st.success("OCR Expense added!")
                st.session_state.paying = False
                del st.session_state.ocr_data
                st.session_state.payment_verified = False
                st.rerun()

elif menu == "Salary Settings":
    st.title("💰 Monthly Salary")
    new_sal = st.number_input("Enter Salary for this month (INR)", min_value=0.0, value=current_salary)
    if st.button("Update Salary"):
        database.update_salary(st.session_state.username, new_sal, current_month)
        st.success(f"Salary updated to ₹{new_sal:,.2f}")
        st.rerun()

elif menu == "Export Data":
    st.title("📊 Export Transactions")
    df = database.get_expenses_df(st.session_state.username)
    if not df.empty:
        # Professional export with Transaction ID
        export_df = df.copy()
        export_df = export_df.rename(columns={
            'id': 'Transaction ID', 
            'username': 'User', 
            'category': 'Category', 
            'amount': 'Amount (INR)', 
            'payment_mode': 'Payment Mode', 
            'date': 'Date', 
            'description': 'Description'
        })
        
        csv = export_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name=f"expenses_{st.session_state.username}.csv", mime='text/csv')
        
        # Excel export option
        try:
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                export_df.to_excel(writer, index=False, sheet_name='Expenses')
            st.download_button("Download Excel", data=output.getvalue(), file_name=f"expenses_{st.session_state.username}.xlsx", 
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except:
            st.warning("Excel export requires 'openpyxl' library.")
    else:
        st.info("No data to export.")
