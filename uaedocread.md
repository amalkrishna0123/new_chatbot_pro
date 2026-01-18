File 1 (syam emirates ID New (1).pdf):

Page 1: Emirates ID Front (Name, ID, Dates).

Page 2: Emirates ID Back (MRZ code, Employer).

File 2 (196850_compressed.pdf):

Page 1: Residence Visa (Contains similar data but is not the ID card).

Page 2: Emirates ID Front.

Page 3: Emirates ID Back.

Page 4: Passport copy.

The Challenge: Standard OCR scripts often fail here because they read Page 1 of File 2 (the Visa) and mistake it for the ID, or they get confused by the Passport data.

Solution Strategy
To handle "unordered" and "non-clear" pages robustly, the codebase below uses a pattern-matching approach (Regex) rather than position-based extraction.

OCR Processing: It sends the full PDF to the OCR.space API.

Page Filtering: It iterates through every page but only processes text blocks that contain the specific Emirates ID pattern (784-XXXX-XXXXXXX-X). This automatically ignores Passports and Visas.

Data Cleaning: It uses regular expressions to hunt for keywords ("Name", "Date of Birth", "Nationality") regardless of where they appear on the page.

Python Codebase
You will need the requests library. You can install it via pip install requests.

Python

import requests
import json
import re

class EmiratesIDExtractor:
    def __init__(self, api_key='helloworld'):
        """
        Initialize with your OCR.space API key.
        Get a free key at https://ocr.space/ocrapi
        """
        self.api_key = api_key
        self.api_url = 'https://api.ocr.space/parse/image'

    def ocr_file(self, file_path):
        """Sends the PDF to OCR.space and returns the JSON response."""
        try:
            with open(file_path, 'rb') as f:
                payload = {
                    'apikey': self.api_key,
                    'isOverlayRequired': False,
                    'detectOrientation': True,
                    'scale': True,
                    'OCREngine': 2, # Engine 2 is better for numbers/IDs
                    'language': 'eng'
                }
                files = {'file': f}
                response = requests.post(self.api_url, files=files, data=payload)
                return response.json()
        except Exception as e:
            return {"error": str(e)}

    def clean_text(self, text):
        """Cleans OCR artifacts (extra spaces, newlines)."""
        # Remove multiple spaces and newlines for regex matching
        return " ".join(text.split())

    def parse_id_details(self, ocr_result):
        """
        Iterates through all pages and extracts data ONLY if valid ID patterns are found.
        """
        if ocr_result.get('IsErroredOnProcessing'):
            return {"error": ocr_result.get('ErrorMessage')}

        extracted_data = {
            "id_number": None,
            "name": None,
            "dob": None,
            "nationality": None,
            "expiry_date": None,
            "card_number": None
        }

        parsed_results = ocr_result.get('ParsedResults', [])

        for page in parsed_results:
            raw_text = page.get('ParsedText', '')
            clean = self.clean_text(raw_text)
            
            # --- STRATEGY: Regex Pattern Matching ---
            
            # 1. ID Number (Format: 784-XXXX-XXXXXXX-X)
            # This is the "Anchor". If this isn't found, we assume it's not the Front of an ID.
            id_match = re.search(r'784\s?-\s?(\d{4})\s?-\s?(\d{7})\s?-\s?(\d{1})', clean)
            if id_match:
                extracted_data["id_number"] = f"784-{id_match.group(1)}-{id_match.group(2)}-{id_match.group(3)}"

                # 2. Name (Looks for 'Name' followed by text, stops at 'Date of Birth' or dates)
                # Matches "Name: John Doe" or just "Name John Doe"
                name_match = re.search(r'Name[:\s]+([A-Za-z\s]+?)(?=\s*Date of Birth|\s*Nationality|\s*\d{2}/\d{2}/\d{4})', clean, re.IGNORECASE)
                if name_match:
                    extracted_data["name"] = name_match.group(1).strip()

                # 3. Nationality (Looks for 'Nationality' followed by text)
                nat_match = re.search(r'Nationality[:\s]+([A-Za-z\s]+?)(?=\s*Signature|\s*Issuing|\s*\d{2}/\d{2})', clean, re.IGNORECASE)
                if nat_match:
                    extracted_data["nationality"] = nat_match.group(1).strip()
                
                # 4. Dates (Finds all dates in DD/MM/YYYY format)
                # Usually, the first date after DOB is DOB, the future date is Expiry.
                dates = re.findall(r'\d{2}/\d{2}/\d{4}', clean)
                if dates:
                    # Logic: Expiry is usually the latest date, DOB is the earliest (usually)
                    # A safer bet is strictly looking for keywords, but OCR often messes up layout.
                    # This is a heuristic fallback:
                    from datetime import datetime
                    try:
                        date_objs = sorted([datetime.strptime(d, "%d/%m/%Y") for d in dates])
                        extracted_data["dob"] = date_objs[0].strftime("%d/%m/%Y") # Earliest
                        extracted_data["expiry_date"] = date_objs[-1].strftime("%d/%m/%Y") # Latest
                    except:
                        pass

            # 5. Card Number (Usually on the BACK of the card)
            # Format: 9 digits usually, distinct from ID number. 
            # Looking for "Card Number" label.
            card_match = re.search(r'Card Number[:\s]+(\d{9})', clean, re.IGNORECASE)
            if card_match:
                extracted_data["card_number"] = card_match.group(1)

        return extracted_data

# --- USAGE EXAMPLE ---
if __name__ == "__main__":
    # Replace with your actual file paths
    files_to_process = ["syam emirates ID New (1).pdf", "196850_compressed.pdf"]
    
    extractor = EmiratesIDExtractor(api_key='helloworld') # Use 'helloworld' for testing

    for file_name in files_to_process:
        print(f"--- Processing: {file_name} ---")
        
        # 1. Get OCR Result
        ocr_json = extractor.ocr_file(file_name)
        
        # 2. Extract Data
        data = extractor.parse_id_details(ocr_json)
        
        print(json.dumps(data, indent=2))
Key Technical Notes
OCR Engine 2: In the payload, I set 'OCREngine': 2. This is crucial. OCR.space has two engines; Engine 2 is significantly better at extracting numbers and special characters from ID cards than Engine 1.

Regex vs. Coordinate Parsing: Previous attempts likely failed because they tried to read text at specific X/Y coordinates (e.g., "Top Right"). Since your pages are unordered (Page 1 vs Page 2), coordinate parsing breaks. The Regex approach works by searching the entire text stream for the 784- pattern. If it finds it, it assumes that text block is an ID and processes it.

Date Logic: The script grabs all dates (DD/MM/YYYY) on the ID page and sorts them. The earliest is typically the Date of Birth, and the latest is the Expiry Date. This handles cases where the text "Date of Birth" is too blurry to read, but the numbers 07/03/1988 are clear.