import requests
import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EmiratesIDExtractor:
    def __init__(self, api_key='K82681714188957'): # Default free key for testing
        """
        Initialize with your OCR.space API key.
        """
        self.api_key = api_key
        self.api_url = 'https://api.ocr.space/parse/image'
        
        # Regex patterns for fields
        self.labels = {
            # ID: Matches 784 followed by 15 digits, with optional dashes or spaces
            'emirates_id': re.compile(r'784[\s-]?(\d{4})[\s-]?(\d{7})[\s-]?(\d{1})'),
            
            # Nationality: Handles "United Kingdom (UK)" and standard text
            'nationality': re.compile(r'(?:Nationality|Nationalit[eéy])[\s\:\.]*([A-Za-z\s\(\)]{3,30})', re.IGNORECASE),
            
            # Gender: Standard M/F check
            'gender': re.compile(r'(?:Sex|Gender|Gen\.)(?:[:\s]+)(M|F|Male|Female)', re.IGNORECASE),
            
            # Employer/Sponsor: Greedy capture but stops before other known fields
            'employer': re.compile(r'(?:Employer|Company|Sponsor)(?:[\s\/]*(?:Name|Title))?[\s\:\.]*(.{3,50}?)[\s]*(?=(?:Occupation|Profession|Job|ID|Date|Sex|Nationality|Place|Issue|Expiry|$))', re.IGNORECASE),
            
            # Occupation: Similar logic to employer
            'occupation': re.compile(r'(?:Occupation|Profession|Job|Desig\.)(?:[:\s]+)(.{3,50}?)(?=\s*(?:Employer|Sponsor|ID|Date|Sex|Nationality|Place)|$)', re.IGNORECASE),
            
            # Issuing Place
            'issuing_place': re.compile(r'(?:Issuing|Place|Issue)(?:[:\s]+)(Dubai|Abu Dhabi|Sharjah|Ajman|Umm Al Quwain|Ras Al Khaimah|Fujairah)', re.IGNORECASE),
            
            # Dates: Matches DD/MM/YYYY or YYYY/MM/DD
            'dates': re.compile(r'(?:\b)(\d{2}[\/\-\.]\d{2}[\/\-\.]\d{4})|(\d{4}[\/\-\.]\d{2}[\/\-\.]\d{2})(?:\b)')
        }

    def ocr_file(self, file_path_or_stream, engine=2) -> Dict[str, Any]:
        """Sends the PDF/Image to OCR.space and returns the JSON response."""
        try:
            payload = {
                'apikey': self.api_key,
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'OCREngine': engine, 
                'language': 'eng'
            }
            
            # Handle file path vs file stream
            if isinstance(file_path_or_stream, str):
                with open(file_path_or_stream, 'rb') as f:
                     response = requests.post(self.api_url, files={'file': f}, data=payload)
            else:
                if hasattr(file_path_or_stream, 'seek'):
                    file_path_or_stream.seek(0)
                
                filename = getattr(file_path_or_stream, 'name', 'upload.pdf')
                # Simple content type guess
                content_type = 'application/pdf'
                if filename.lower().endswith(('.jpg', '.jpeg')): content_type = 'image/jpeg'
                elif filename.lower().endswith('.png'): content_type = 'image/png'

                file_content = file_path_or_stream.read()
                files = {'file': (filename, file_content, content_type)}
                response = requests.post(self.api_url, files=files, data=payload)

            if response.status_code != 200:
                return {"error": f"OCR API Error: {response.status_code}"}
            
            try:
                result = response.json()
                # DEBUG: Print raw response to see why it fails
                print(f"DEBUG: OCR API Response: {json.dumps(result)}") 
                return result
            except json.JSONDecodeError:
                 return {"error": f"Invalid JSON from OCR API: {response.text}"}
            
        except Exception as e:
            logger.error(f"OCR Request Failed: {e}")
            return {"error": str(e)}

    def clean_text(self, text: str) -> str:
        """Cleans OCR artifacts."""
        if not text: return ""
        return " ".join(text.split())

    def _enhance_name_extraction(self, extracted_name: str, full_text: str) -> str:
        """
        Enhances name extraction by checking for title case names on previous lines.
        Handles cases where the name is split across lines like:
        - "Ismaeel Sajaad Muhammad Sajaad Manakkat"
        - "Name: Thekke Peedikayil"
        """
        if not extracted_name or not full_text:
            return extracted_name
        
        # Normalize text and split into lines
        normalized = full_text.replace('\r', '\n')
        lines = [l.strip() for l in normalized.splitlines() if l.strip()]
        
        # Find the line containing the extracted name
        # Prefer lines with "Name:" label, but fall back to any line containing the name
        name_line_idx = -1
        for idx, line in enumerate(lines):
            # Check if extracted name appears in this line (case-insensitive)
            if extracted_name.lower() in line.lower():
                # If this line has "Name:" label, use it immediately (most likely the correct one)
                if 'name:' in line.lower():
                    name_line_idx = idx
                    break
                # Otherwise, remember the first match but keep searching
                elif name_line_idx == -1:
                    name_line_idx = idx
        
        # If we found the name line and there's a previous line, check it
        if name_line_idx > 0:
            prev_line = lines[name_line_idx - 1]
            
            # List of terms that should NEVER be part of a name
            invalid_terms = [
                'property owner', 'occupation', 'employer', 'sponsor', 'investors',
                'entrepreneurs', 'specialized', 'file', 'number', 'date', 'expiry',
                'issuing', 'nationality', 'gender', 'sex', 'male', 'female',
                'resident', 'identity', 'card', 'id', 'passport', 'signature',
                'united', 'arab', 'emirates', 'federal', 'authority'
            ]
            
            # Check if previous line looks like a name part:
            # 1. Has at least 2 words (names are usually multi-word)
            # 2. No digits
            # 3. No invalid keywords
            # 4. Starts with uppercase (title case) or is mostly uppercase
            # 5. Mostly letters (not special characters)
            
            words = prev_line.split()
            if len(words) >= 2:  # At least 2 words
                # Check for digits
                if not any(ch.isdigit() for ch in prev_line):
                    # Check for invalid terms
                    prev_lower = prev_line.lower()
                    if not any(term in prev_lower for term in invalid_terms):
                        # Check if it starts with uppercase (title case) or is mostly uppercase
                        starts_upper = prev_line and prev_line[0].isupper()
                        upper_chars = sum(1 for c in prev_line if c.isupper())
                        total_letters = sum(1 for c in prev_line if c.isalpha())
                        
                        # Accept if: starts with uppercase AND looks like title case or all-caps
                        # Title case: roughly one uppercase per word (e.g., 5 words = ~5 uppercase letters)
                        # All-caps: most letters are uppercase (70%+)
                        if total_letters > 0:
                            upper_ratio = upper_chars / total_letters
                            word_count = len(words)
                            
                            # Title case check: uppercase count should be roughly equal to word count
                            # (each word typically starts with one uppercase letter)
                            # Allow some variance: between 0.7x and 2x word count
                            is_title_case = (
                                starts_upper and 
                                word_count * 0.7 <= upper_chars <= word_count * 2
                            )
                            # All-caps check: mostly uppercase
                            is_mostly_upper = upper_ratio >= 0.7
                            
                            if is_title_case or is_mostly_upper:
                                # Combine previous line with extracted name
                                combined = f"{prev_line} {extracted_name}"
                                logger.info(f"Enhanced name extraction: '{extracted_name}' -> '{combined}'")
                                return combined
        
        return extracted_name

    def parse_mrz(self, text: str) -> Dict[str, Any]:
        """
        Attempts to extract data from the Machine Readable Zone (MRZ) usually found 
        at the bottom of the back of the ID.
        Format roughly:
        I<ARE...
        YYMMDD... (DOB) ... YYMMDD... (Expiry)
        NAME<<...
        """
        mrz_data = {}
        
        # Look for the long alphanumeric strings characteristic of MRZ
        # Line 1 usually contains ID number: I<ARE or ILARE followed by numbers
        # Line 2 usually contains dates: 851009 (YYMMDD)
        # Line 3 usually contains Name: NAME<<NAME
        
        lines = text.split()
        mrz_lines = [line for line in lines if len(line) > 20 and '<' in line or 'ARE' in line]
        
        for line in mrz_lines:
            # 1. Try to capture Name from MRZ (Format: SURNAME<<GIVEN<NAMES)
            if '<<' in line and not any(char.isdigit() for char in line):
                clean_mrz_name = line.replace('<', ' ').strip()
                if len(clean_mrz_name) > 3:
                    mrz_data['full_name'] = clean_mrz_name.title()

            # 2. Try to capture DOB and Expiry from the numeric line
            # Standard MRZ Line 2: YYMMDD(DOB) + 1 digit + Sex + YYMMDD(Expiry)
            # Regex: 6 digits (DOB) + 1 digit + M/F + 6 digits (Expiry)
            date_match = re.search(r'(\d{6})\d([MF])(\d{6})', line)
            if date_match:
                try:
                    dob_str = date_match.group(1)
                    sex_str = date_match.group(2)
                    exp_str = date_match.group(3)
                    
                    # Parse DOB
                    dob = datetime.strptime(dob_str, "%y%m%d")
                    # Fix century (assuming no one is born in future or 1920s with this ID)
                    if dob.year > datetime.now().year:
                        dob = dob.replace(year=dob.year - 100)
                    mrz_data['date_of_birth'] = dob.strftime("%Y-%m-%d")
                    
                    # Parse Expiry
                    exp = datetime.strptime(exp_str, "%y%m%d")
                    mrz_data['expiry_date'] = exp.strftime("%Y-%m-%d")
                    
                    # Parse Sex
                    mrz_data['gender'] = 'Male' if sex_str == 'M' else 'Female'
                    
                except ValueError:
                    pass
                    
        return mrz_data

    def process_pdf(self, file_path_or_stream, employment_type='Employee') -> Dict[str, Any]:
        """
        Main extraction logic using standardized robust parser.
        """
        # 1. OCR Processing
        ocr_result = self.ocr_file(file_path_or_stream, engine=2)
        
        # If engine 2 fails or returns no text, try engine 1
        if not ocr_result.get('ParsedResults'):
            logger.warning("Engine 2 failed, retrying with Engine 1...")
            ocr_result = self.ocr_file(file_path_or_stream, engine=1)

        parsed_results = ocr_result.get('ParsedResults', [])
        if not parsed_results:
             return {"error": "OCR failed to extract text."}

        # 2. Build Corpus
        # Preserve newlines for multi-line name detection (like Document Test)
        full_text_corpus = ""
        for page in parsed_results:
            page_text = page.get('ParsedText', '')
            if page_text:
                # Normalize line endings but preserve line structure
                page_text = page_text.replace('\r', '\n')
                full_text_corpus += "\n" + page_text

        # 3. Use Robust Parser (imported from document_tests)
        try:
            from document_tests.views import parse_fields, parse_back_side_fields
            
            # Extract front and back fields
            front_fields = parse_fields(full_text_corpus)
            back_fields = parse_back_side_fields(full_text_corpus)
            
            # Merge results (Back fields override front if duplicate, usually clearer)
            extracted_data = {**front_fields, **back_fields}
            
            # Enhanced name extraction: Handle title case names on previous line
            # This fixes cases where name is split like:
            # "Ismaeel Sajaad Muhammad Sajaad Manakkat"
            # "Name: Thekke Peedikayil"
            if extracted_data.get('name'):
                extracted_data['name'] = self._enhance_name_extraction(
                    extracted_data.get('name'), 
                    full_text_corpus
                )
            
            # Helper to convert various date formats to YYYY-MM-DD
            def clean_date(date_str):
                if not date_str: return None
                try:
                    # Case 1: DD/MMM/YYYY (e.g. 14/Mar/1990) - output from parse_fields
                    if re.match(r'\d{1,2}/[A-Za-z]{3}/\d{4}', date_str):
                        return datetime.strptime(date_str, "%d/%b/%Y").strftime("%Y-%m-%d")
                    
                    # Case 2: DD/MM/YYYY
                    if re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_str):
                        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                    
                    # Case 3: YYYY-MM-DD (Already correct)
                    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                        return date_str
                        
                    return date_str
                except Exception as e:
                    logger.warning(f"Date conversion failed for {date_str}: {e}")
                    return None # Return None if conversion fails to avoid serializer errors

            # Map robust parser keys to expected schema
            final_data = {
                'emirates_id': extracted_data.get('emirates_id'),
                'full_name': extracted_data.get('name'),
                'date_of_birth': clean_date(extracted_data.get('dob')),
                'issuing_date': clean_date(extracted_data.get('issuing_date')),
                'expiry_date': clean_date(extracted_data.get('expiry_date')),
                'nationality': extracted_data.get('nationality'),
                'gender': extracted_data.get('gender'),
                'issuing_place': extracted_data.get('issuing_place'),
                'occupation': extracted_data.get('occupation'),
                'sponsor_name': extracted_data.get('employer'), # Map employer to sponsor_name preference
            }
            
            # Fallback for Sponsor Name if missing
            if not final_data.get('sponsor_name'):
                final_data['sponsor_name'] = extracted_data.get('sponsor')

            return final_data

        except ImportError:
            # Fallback to legacy regex method if import fails
            logger.error("Could not import parse_fields from document_tests. Using legacy method.")
            return self._legacy_regex_extraction(full_text_corpus)

    def _legacy_regex_extraction(self, full_text_corpus):
        """Legacy method kept as fail-safe"""
        extracted_data = {}

        # 3. Strategy A: MRZ Extraction (Most Reliable)
        mrz_data = self.parse_mrz(full_text_corpus)
        extracted_data.update(mrz_data)

        # 4. Strategy B: Regex Extraction (Fills gaps)

        # ID Number
        if 'emirates_id' not in extracted_data:
            id_match = self.labels['emirates_id'].search(full_text_corpus)
            if id_match:
                extracted_data['emirates_id'] = f"784-{id_match.group(1)}-{id_match.group(2)}-{id_match.group(3)}"

        # Name (If not found in MRZ)
        if 'full_name' not in extracted_data:
            # Look for "Name:" pattern
            name_match = re.search(r'(?:Name|Name\s*:)\s*((?!Profession|Sponsor|Issue|Expiry|Date|Code)[A-Za-z\s]+?)(?=\s*(?:Date|Nationality|ID|Sex|Gender|Signature)|$)', full_text_corpus, re.IGNORECASE)
            if name_match:
                extracted_data['full_name'] = name_match.group(1).strip()

        # Nationality
        if 'nationality' not in extracted_data:
            nat_match = self.labels['nationality'].search(full_text_corpus)
            if nat_match:
                val = nat_match.group(1).strip()
                val = re.split(r'(?:Signature|Issuing|Date|ID)', val, flags=re.IGNORECASE)[0]
                extracted_data['nationality'] = val.strip()

        # Gender
        if 'gender' not in extracted_data:
            g_match = self.labels['gender'].search(full_text_corpus)
            if g_match:
                g = g_match.group(1).lower()
                extracted_data['gender'] = 'Male' if g.startswith('m') else 'Female'

        # Occupation
        if 'occupation' not in extracted_data:
            occ_match = self.labels['occupation'].search(full_text_corpus)
            if occ_match:
                extracted_data['occupation'] = occ_match.group(1).strip()

        # Issuing Place
        if 'issuing_place' not in extracted_data:
            place_match = self.labels['issuing_place'].search(full_text_corpus)
            extracted_data['issuing_place'] = place_match.group(1).strip() if place_match else 'Dubai'

        # Sponsor/Employer
        employer_match = self.labels['employer'].search(full_text_corpus)
        if employer_match:
            sponsor_val = employer_match.group(1).strip()
            if len(sponsor_val) > 3:
                extracted_data['sponsor_name'] = sponsor_val

        # 5. Date Parsing
        all_dates = []
        raw_date_matches = self.labels['dates'].findall(full_text_corpus)
        
        for match in raw_date_matches:
            date_str = match[0] if match[0] else match[1]
            try:
                if '-' in date_str: date_str = date_str.replace('-', '/')
                if '.' in date_str: date_str = date_str.replace('.', '/')
                
                parts = date_str.split('/')
                if len(parts[0]) == 4: # YYYY/MM/DD
                    dt = datetime.strptime(date_str, "%Y/%m/%d")
                else: # DD/MM/YYYY
                    dt = datetime.strptime(date_str, "%d/%m/%Y")
                
                all_dates.append(dt)
            except ValueError:
                continue

        if all_dates:
            unique_dates = sorted(list(set(all_dates)))
            
            if 'date_of_birth' not in extracted_data and len(unique_dates) > 0:
                extracted_data['date_of_birth'] = unique_dates[0].strftime("%Y-%m-%d")
            
            if 'expiry_date' not in extracted_data and len(unique_dates) > 1:
                extracted_data['expiry_date'] = unique_dates[-1].strftime("%Y-%m-%d")
                
            if 'issuing_date' not in extracted_data:
                if len(unique_dates) >= 3:
                    issue_candidates = [d for d in unique_dates if d != unique_dates[0] and d != unique_dates[-1]]
                    if issue_candidates:
                        extracted_data['issuing_date'] = issue_candidates[0].strftime("%Y-%m-%d")

        return extracted_data