import google.generativeai as genai
import json
import os
from PIL import Image

SYSTEM_PROMPT = """
You are a professional Financial Advisor AI for the 'AI Expense Tracker' application. 
Your goal is to help users manage their money, provide budgeting tips, and analyze their spending habits.
Keep your tone helpful, professional, and encouraging.
You have access to the user's current balance and recent transaction history provided in the context.
Always give actionable advice in INR (₹).
"""

def configure_gemini(api_key):
    if not api_key:
        return False
    try:
        genai.configure(api_key=api_key)
        # Test connection
        model = genai.GenerativeModel('gemini-1.5-flash')
        model.generate_content("ping")
        return True
    except Exception as e:
        print(f"Gemini Configuration Error: {e}")
        return False

def get_gemini_response(prompt, history=None, api_key=None):
    """
    Standard chat response from Gemini with history support.
    """
    if api_key:
        genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=SYSTEM_PROMPT
        )
        
        # Convert Streamlit history format to Gemini format if necessary
        formatted_history = []
        if history:
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                formatted_history.append({"role": role, "parts": [msg["content"]]})
        
        chat = model.start_chat(history=formatted_history)
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        err_msg = str(e)
        if "API_KEY_INVALID" in err_msg:
            return "❌ **Invalid API Key!** Please check your key in the sidebar. Make sure you copied the correct string from Google AI Studio."
        return f"Error connecting to Gemini: {err_msg}"

def extract_receipt_data_gemini(image_path, api_key=None):
    """
    Uses Gemini Vision to extract structured data from a receipt.
    """
    if api_key:
        genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(image_path)
        
        prompt = """
        Analyze this receipt and extract the following information in JSON format:
        {
            "amount": float,
            "date": "YYYY-MM-DD",
            "category": "One of: Food, Travel, Shopping, Groceries, Entertainment, Health, Others",
            "description": "Short description of items or vendor",
            "currency": "e.g. INR, USD"
        }
        Only return the raw JSON. No markdown blocks.
        """
        
        response = model.generate_content([prompt, img])
        json_text = response.text.strip()
        
        # Clean potential markdown
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(json_text)
    except Exception as e:
        print(f"Gemini OCR Error: {e}")
        return None
