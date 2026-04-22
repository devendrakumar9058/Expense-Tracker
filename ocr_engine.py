import easyocr
import re
import gemini_service
import os

def extract_data_from_image(image_path, api_key=None):
    """
    Extracts Amount and potential Date from a receipt image.
    Uses Gemini if API key is provided, falls back to EasyOCR.
    """
    # Try Gemini first if API key is available
    if api_key:
        gemini_data = gemini_service.extract_receipt_data_gemini(image_path, api_key=api_key)
        if gemini_data:
            return {
                "amount": float(gemini_data.get('amount', 0) or 0),
                "date": gemini_data.get('date', ""),
                "category": gemini_data.get('category', "Others"),
                "description": gemini_data.get('description', "OCR Scan"),
                "raw_text": str(gemini_data),
                "source": "Gemini AI"
            }

    # Fallback to EasyOCR
    try:
        reader = easyocr.Reader(['en'])
        result = reader.readtext(image_path, detail=0)
        
        text = " ".join(result).lower()
        
        # Simple regex for finding amounts
        amount_patterns = [
            r"total\s*[:\s]*(\d+\.\d{2})",
            r"net\s*amt\s*[:\s]*(\d+\.\d{2})",
            r"amount\s*[:\s]*(\d+\.\d{2})",
            r"(\d+\.\d{2})"
        ]
        
        found_amount = 0.0
        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                found_amount = float(match.group(1))
                break
        
        # Simple regex for finding dates
        date_pattern = r"(\d{2}[/-]\d{2}[/-]\d{4})"
        date_match = re.search(date_pattern, text)
        found_date = date_match.group(1) if date_match else ""
        
        return {
            "amount": found_amount,
            "date": found_date,
            "raw_text": text,
            "source": "EasyOCR (Basic)"
        }
    except Exception as e:
        print(f"OCR Error: {e}")
        return None

def predict_category(text):
    # This is only used as a fallback for EasyOCR results
    categories = {
        "Food": ["restaurant", "cafe", "hotel", "burger", "pizza", "coffee", "lunch", "dinner"],
        "Groceries": ["mart", "store", "market", "rely", "fresh", "milk"],
        "Shopping": ["fashion", "clothing", "lifestyle", "apparel"],
        "Travel": ["uber", "ola", "taxi", "fuel", "petrol", "diesel", "train", "flight"],
        "Others": []
    }
    
    for cat, keywords in categories.items():
        for keyword in keywords:
            if keyword in text.lower():
                return cat
    return "Others"
