from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


# -------------------- Mindee Passport Upload (Testing Version) --------
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from mindee import ClientV2, InferenceParameters, BytesInput
import re

from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from rest_framework.decorators import api_view, authentication_classes, permission_classes

# @csrf_exempt
# @api_view(["POST"])
# @permission_classes([AllowAny])
# @api_view(['POST'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])
@api_view(['POST'])
@authentication_classes([])   # ⬅️ disable auth
@permission_classes([AllowAny])
def passport_upload(request):
    print(f"--- [PASSPORT] Request Received ---")
    
    try:
        uploaded = request.FILES.get("file")
        if not uploaded:
            print(f"--- [PASSPORT] Error: No file uploaded ---")
            return JsonResponse({"error": "No file uploaded"}, status=400)

        print(f"--- [PASSPORT] File: {uploaded.name} ({uploaded.size} bytes) ---")

        # Prefer env, fall back to your test keys so nothing breaks while you tinker
        # api_key = "md_0v6CgIEbeCBkiGlyrM-PZ6mL2CkSGF7Pxu28o2P27E0"
        api_key = "md_8a723Te9lQaJXaCMJeBBa860F_sVH4XzXF_kfxoBCmo"
        # model_id = "703498b8-dede-4310-8a5b-fdaf829232be"
        model_id = "941c8dd9-8ab5-4192-ad7a-7311952095e0"

        client = ClientV2(api_key)
        params = InferenceParameters(model_id=model_id, confidence=True)

        # Read uploaded file bytes
        input_source = BytesInput(uploaded.read(), filename=uploaded.name)

        # OCR
        print(f"--- [PASSPORT] Sending to Mindee API... ---")
        response = client.enqueue_and_get_inference(input_source, params)
        print(f"--- [PASSPORT] Mindee Response Received ---")
        fields = response.inference.result.fields

        # Helpers -------------------------------------------------------------

        def value_of(field_obj):
            """
            Mindee returns either raw strings or objects with .value.
            Return a clean string or None.
            """
            if field_obj is None:
                return None
            v = getattr(field_obj, "value", field_obj)
            if v is None:
                return None
            s = str(v).strip()
            return s if s else None

        def get_any(keys):
            for k in keys:
                if k in fields:
                    v = value_of(fields[k])
                    if v:
                        return v
            return None

        def normalize_date(s):
            if not s:
                return None
            s = str(s).strip()
            # Mindee commonly returns YYYY-MM-DD
            m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
            if m:
                y, mm, dd = m.groups()
                return f"{dd}/{mm}/{y}"
            return s

        def _collapse_spaces(txt):
            return re.sub(r"\s+", " ", txt).strip()

        def parse_names_from_mrz(mrz_line_1):
            """
            MRZ line 1 format (with OCR glitches):
            'P<ISSUER[SURNAME]<<GIVEN<NAMES<<<<'
            Real world often has '<' misread as 'A', so handle that too.
            Returns (surname, given_names) or (None, None).
            """
            if not mrz_line_1:
                return None, None

            line = mrz_line_1.upper()
            # Normalize common OCR misreads of the filler char
            line = line.replace("«", "<")
            
            line_no_hdr = re.sub(r"^P[<A][A-Z]{3}", "", line)

            # Split surname and given names by the primary separator
            parts = line_no_hdr.split("<<", 1)
            if len(parts) != 2:
                return None, None

            raw_surname, raw_given = parts[0], parts[1]

            surname = _collapse_spaces(raw_surname.replace("<", " "))
            given = _collapse_spaces(raw_given.split("<<", 1)[0].replace("<", " "))

            return (surname or None), (given or None)

        # --------------------------------------------------------------------

        print(f"--- [PASSPORT] Extracting fields... ---")

        passport_number = get_any(["passport_number", "PassportNumber", "Document Number"])
        dob = normalize_date(get_any(["date_of_birth", "Date of Birth", "DOB"]))

        # Prefer Mindee's plural keys first, then common alternates
        given_name = get_any([
            "given_names", "given_name", "Given Names", "Given Name",
            "first_names", "first_name", "forenames", "forename", "given"
        ])
        surname = get_any([
            "surnames", "surname", "Surname", "Last Name",
            "family_name", "family_names", "lastname"
        ])

        # Fallback via MRZ if any name is missing
        if not given_name or not surname:
            print(f"--- [PASSPORT] Trying MRZ fallback for names... ---")
            mrz1 = get_any(["mrz_line_1", "mrz1", "MRZ Line 1"])
            parsed_surname, parsed_given = parse_names_from_mrz(mrz1)
            surname = surname or parsed_surname
            given_name = given_name or parsed_given

        full_name = _collapse_spaces(f"{given_name or ''} {surname or ''}")

        print(f"--- [PASSPORT] Extraction complete. Passport: {passport_number}, Name: {full_name} ---")

        return JsonResponse({
            "fields": {
                "passport_number": passport_number,
                "given_name": given_name, 
                "surname": surname,
                "name": full_name,
                "dob": dob
            },
            "validation": {
                "is_valid": all([passport_number, full_name, dob]),
                "validation_message": "Successfully extracted passport details"
            }
        }, status=200)

    except Exception as e:
        # Do not leak stack traces to clients
        print(f"--- [PASSPORT] ERROR: {e} ---")
        return JsonResponse({"error": f"OCR failed: {str(e)}"}, status=500)



def parse_fields(text):
    """
    Robust field parser for Emirates ID text.
    Returns a dict with at least possible keys:
      emirates_id, name, address, expiry_date, issuing_date, dob, nationality, sex
    """
    from datetime import datetime

    data = {}
    raw = text or ""
    normalized = raw.replace('\r', '\n')

    # --- COLLECT MULTI-LINE NAME BLOCK (CRITICAL FIX) ---
    name_lines = []
    lines = [l.strip() for l in normalized.splitlines() if l.strip()]

    BLOCK_TERMS = [
        'id', 'identity', 'number', 'card', 'passport',
        'nationality', 'date', 'expiry', 'issuing',
        'sex', 'gender', 'occupation', 'employer',
        'signature', 'place'
    ]

    for line in lines:
        low = line.lower()

        if any(term in low for term in BLOCK_TERMS):
            continue
        if any(ch.isdigit() for ch in line):
            continue
        if len(line.split()) < 2:
            continue

    name_lines.append(line)

    # Join ALL name lines
    if name_lines:
        data['name'] = " ".join(name_lines)

    # mrz_name = extract_name_from_mrz(raw)
    # if mrz_name:
    #     data['name'] = mrz_name

    # Define stopwords once, usable in all branches
    stopwords = [
        'resident', 'identity', 'card', 'id number', 'id no', 'number',
        'nationality', 'date of birth', 'date', 'expiry', 'issuing',
        'signature', 'sex', 'passport', 'signature/', 'issue'
    ]

    # 1) Emirates ID number
    m = re.search(r'\b\d{3}-\d{4}-\d{7}-\d\b', raw)
    if m:
        data['emirates_id'] = m.group(0).strip()

    # 2) Labeled name - improved extraction with strict validation
    # Try multiple patterns to catch name in different formats
    name_patterns = [
        # Pattern 1: Name: James Edward Clough (proper name format with capitals)
        r'(?i)Name\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        # Pattern 2: Name: followed by text until newline or next field (but not including "Name" word)
        r'(?i)Name\s*[:\-]?\s*([A-Z][^\n\r]{1,60}?)(?:\s+Name\s*$|\n|Occupation|Date|Nationality|Expiry|Issuing|Sex|Gender|$)',
        # Pattern 3: Arabic name label
        r'(?i)(?:الاسم|اسم)\s*[:\-]?\s*([^\n\r]{2,80})',
    ]
    
    # List of terms that should NEVER be extracted as name
    invalid_name_terms = [
        'property owner', 'occupation', 'employer', 'sponsor', 'investors',
        'entrepreneurs', 'specialized', 'file', 'number', 'date', 'expiry',
        'issuing', 'nationality', 'gender', 'sex', 'male', 'female'
    ]
    
    for pattern in name_patterns:
        m = re.search(pattern, raw)
        if m:
            name_val = m.group(1).strip()
            # Remove trailing "Name" label if it was captured
            name_val = re.sub(r'\s+Name\s*$', '', name_val, flags=re.IGNORECASE).strip()
            # Clean up common OCR artifacts
            name_val = re.sub(r'[\:\-\/\|]+$', '', name_val).strip()
            # Stop if we hit common field names (occupation, date, etc.)
            name_val = re.split(r'(?i)\s+(?:Occupation|Date|Nationality|Expiry|Issuing|Sex|Gender|Employer|Name\s*$)', name_val)[0].strip()
            
            # STRICT VALIDATION check
            name_lower = name_val.lower()
            if any(term in name_lower for term in invalid_name_terms):
                continue
            
            if re.search(r'\d{4,}', name_val):
                continue

            # --- MULTI-LINE CHECK ---
            # Try to find where this match occurred in the raw text lines
            # This is heuristics since we extracted via regex on full text
            
            # 1. Normalize lines again
            lines = [l.strip() for l in normalized.splitlines() if l.strip()]
            
            # 2. Find the line index containing our match
            start_idx = -1
            for idx, line in enumerate(lines):
                if name_val in line:
                    start_idx = idx
                    break
            
            # --- LOOK BEHIND CHECK (New) ---
            # Scenario: 
            # Ismaeel Sajaad Muhammad Sajaad Manakkat
            # Name: Thekke Peedikayil
            if start_idx > 0:
                prev_line = lines[start_idx - 1]
                # Check if previous line looks like a name part (Uppercase, no digits, no keywords)
                pl_upper = re.sub(r'[^A-Z]', '', prev_line)
                alphanum_ratio = len(pl_upper) / len(prev_line.replace(' ', '')) if prev_line.strip() else 0
                
                is_prev_part = (
                    len(prev_line) > 3 and
                    not any(ch.isdigit() for ch in prev_line) and
                    not any(term in prev_line.lower() for term in invalid_name_terms + stopwords) and
                    alphanum_ratio > 0.8
                )
                
                if is_prev_part:
                    name_val = prev_line + " " + name_val

            # --- LOOK AHEAD CHECK ---
            # 3. Look ahead for continuation lines
            if start_idx != -1 and start_idx + 1 < len(lines):
                # Check next 1-2 lines
                for offset in range(1, 3):
                    if start_idx + offset >= len(lines): break
                    
                    next_line = lines[start_idx + offset]
                    
                    # Validation for continuation line:
                    # - Must be uppercase (Emirates ID names are typically uppercase)
                    # - No digits
                    # - No labels
                    # - No special characters indicating a new section
                    
                    nl_upper = re.sub(r'[^A-Z]', '', next_line) # Only letters
                    alphanum_ratio = len(nl_upper) / len(next_line.replace(' ', '')) if next_line.strip() else 0
                    
                    is_continuation = (
                        len(next_line) > 3 and
                        not any(ch.isdigit() for ch in next_line) and
                        not any(term in next_line.lower() for term in invalid_name_terms + stopwords) and
                        alphanum_ratio > 0.8  # mostly letters
                    )
                    
                    if is_continuation:
                        name_val += " " + next_line
                    else:
                        break # Stop if a line doesn't match

            data['name'] = name_val
            break

    # 3) Fallback name detection if not found
    if 'name' not in data or not data['name']:
        lines = [l.strip() for l in normalized.splitlines() if l.strip()]
        candidate = None
        for idx, line in enumerate(lines):
            low = line.lower()
            if any(sw in low for sw in stopwords):
                continue
            if any(ch.isdigit() for ch in line):
                continue
            # Skip common occupation/employer terms
            if any(term in low for term in ['property owner', 'occupation', 'employer', 'sponsor']):
                continue
            if len(line.split()) >= 2 and len(line) > 3:
                if 'united arab emirates' in low or 'arab emirates' in low:
                    continue
                name_candidate = line
                if idx + 1 < len(lines):
                    nxt = lines[idx + 1]
                    if (not any(sw in nxt.lower() for sw in stopwords)
                        and not any(ch.isdigit() for ch in nxt)
                        and len(nxt.split()) <= 3
                        and 'occupation' not in nxt.lower()
                        and 'employer' not in nxt.lower()):
                        name_candidate = name_candidate + ' ' + nxt
                candidate = name_candidate
                break
        # if candidate:
        #     # data['name'] = candidate
        #     data.setdefault('raw_name_candidates', []).append(candidate)

    
    # 4) Post-process name to ensure it's not occupation or other field
    # This validation happens AFTER all fields are extracted
    invalid_name_terms = ['property owner', 'occupation', 'owner', 'employer', 'sponsor']
    
    if 'name' in data:
        name_lower = data['name'].lower()
        # If name contains invalid terms, clear it and try to find the real name
        if any(term in name_lower for term in invalid_name_terms):
            # Clear the invalid name
            data.pop('name', None)
            
            # Try to find name by looking for pattern: Name: [Proper Name]
            # Look for lines that have "Name:" followed by a proper name format
            lines = [l.strip() for l in normalized.splitlines() if l.strip()]
            for idx, line in enumerate(lines):
                if re.search(r'(?i)^Name\s*[:\-]', line):
                    # Found a Name: line, extract the name part
                    name_match = re.search(r'(?i)Name\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', line)
                    if name_match:
                        potential_name = name_match.group(1).strip()
                        # Validate it's not an occupation term
                        if not any(term in potential_name.lower() for term in invalid_name_terms):
                            data['name'] = potential_name
                            break
                    
                    # If not found in same line, check next line
                    if idx + 1 < len(lines):
                        next_line = lines[idx + 1].strip()
                        # Check if next line looks like a name (capitalized words, no occupation terms)
                        if (re.search(r'^[A-Z][a-z]+', next_line) and 
                            not any(term in next_line.lower() for term in invalid_name_terms) and
                            len(next_line.split()) >= 2):
                            data['name'] = next_line
                            break
    
    # Final check: if we have both name and occupation, ensure they're not swapped
    if 'name' in data and 'occupation' in data:
        name_lower = data['name'].lower()
        occ_lower = data['occupation'].lower()
        
        # If name looks like occupation and occupation looks like a name, swap them
        if (any(term in name_lower for term in invalid_name_terms) and
            not any(term in occ_lower for term in invalid_name_terms) and
            re.search(r'[A-Z][a-z]', data['occupation'])):
            # Swap them
            data['name'], data['occupation'] = data['occupation'], data['name']

    # 4) Dates
    date_pattern = r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})'
    all_dates = re.findall(date_pattern, raw)

    def find_date_by_labels(labels):
        for lbl in labels:
            m = re.search(r'(?i)' + lbl + r'\s*[:\-]?\s*' + date_pattern, raw)
            if m:
                return m.group(1)
        return None

    dob = find_date_by_labels(['Date of Birth', 'DOB', 'Birth', 'تاريخ الميلاد'])
    issuing = find_date_by_labels([
    'Issuing Date', 'Issue Date', 'Issuing', 'Date of Issue',
    'تاريخ الإصدار'
    ])
    expiry = find_date_by_labels(['Expiry Date', 'Expiry', 'تاريخ الانتهاء'])

    # Convert dates to DD/MMM/YYYY format if found
    def format_date(date_str):
        try:
            # Handle different separators
            if '/' in date_str:
                day, month, year = date_str.split('/')
            elif '-' in date_str:
                day, month, year = date_str.split('-')
            else:
                return date_str
                
            # Convert to proper format
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            if month.isdigit() and 1 <= int(month) <= 12:
                month = month_names[int(month) - 1]
            return f"{day}/{month}/{year}"
        except:
            return date_str

    if dob:
        data['dob'] = format_date(dob)
    if issuing:
        data['issuing_date'] = format_date(issuing)
    if expiry:
        data['expiry_date'] = format_date(expiry)
    if 'expiry_date' not in data and all_dates:
        data['expiry_date'] = format_date(all_dates[-1])
    if not issuing and all_dates:
        # Heuristic: first date is DOB, second is Issuing, last is Expiry
        if len(all_dates) >= 2:
            data["issuing_date"] = format_date(all_dates[1])

    # 6) Nationality
    # Improved pattern: Capture letters, spaces, parens (for "United Kingdom (UK)")
    m = re.search(r'(?i)(?:Nationality|الجنسية)\s*[:\-]?\s*([A-Za-z\s\(\)\-]{3,60})', raw)
    if m:
        nat_val = m.group(1).strip()
        
        # Stop at common next-field headers that might have been captured
        # Split by: Issuing, Date, Expiry, Sex, Gender, ID, Number, Employer, Occupation
        stop_pattern = r'(?i)\s+(?:Issuing|Issue|Date|Expiry|Sex|Gender|ID|No|Number|Employer|Occupation|Place)'
        
        # Take the first part before any of these keywords
        clean_nat = re.split(stop_pattern, nat_val)[0].strip()
        
        # Double check: split by double spaces if OCR put another field on same line (e.g. SOMALIA  01/01/2025)
        parts = re.split(r'\s{2,}', clean_nat)
        if parts:
            data['nationality'] = parts[0].strip()
        else:
            data['nationality'] = clean_nat

    # 7) Sex / Gender
    gender_patterns = [
        r'(?i)(?:Sex|Gender|الجنس)\s*[:\-]?\s*(Male|Female|M|F|ذكر|أنثى)',
        r'(?i)(?:Sex|Gender|الجنس)\s*[:\-]?\s*([^\n]{1,20})',
        r'(?i)(SCANNE|SCANNED|SCAN|SCANNING)',
    ]

    gender_val = None
    for pattern in gender_patterns:
        m = re.search(pattern, raw)
        if m:
            val = m.group(1).strip() if m.group(1) else ""
            if val and not any(word in val.upper() for word in ['SCAN', 'SCANNED', 'SCANNING']):
                gender_val = val
                break
    
    # If we found a gender value, normalize it
    if gender_val:
        val = gender_val.upper()
        if val in ["M", "MALE", "ذكر"]:
            data["gender"] = "Male"
            data["sex"] = "Male"
        elif val in ["F", "FEMALE", "أنثى"]:
            data["gender"] = "Female"
            data["sex"] = "Female"
        else:
            data["gender"] = gender_val
            data["sex"] = gender_val


    # 8) Address
    m = re.search(r'(?i)(?:Address|العنوان)\s*[:\-]?\s*([^\n\r]{2,140})', raw)
    if m:
        data['address'] = m.group(1).strip()
    else:
        if 'nationality' in data:
            lines = [l.strip() for l in normalized.splitlines() if l.strip()]
            for idx, line in enumerate(lines):
                if data['nationality'].lower() in line.lower():
                    if idx + 1 < len(lines):
                        cand = lines[idx + 1]
                        if len(cand) > 4 and not any(ch.isdigit() for ch in cand):
                            data['address'] = cand
                            break
        if 'address' not in data:
            lines = [l.strip() for l in normalized.splitlines() if l.strip()]
            for l in reversed(lines):
                low = l.lower()
                if any(sw in low for sw in stopwords):
                    continue
                if any(ch.isdigit() for ch in l):
                    continue
                if len(l.split()) >= 2:
                    data['address'] = l
                    break

    for k, v in list(data.items()):
        if isinstance(v, str):
            v = v.strip().rstrip(':').strip()
            # Special cleanup for name field
            if k == 'name':
                # Remove trailing "Name" label if present
                v = re.sub(r'\s+Name\s*$', '', v, flags=re.IGNORECASE).strip()
                # Normalize all-caps names to proper case (JAMES EDWARD -> James Edward)
                if v.isupper() and len(v.split()) > 1:
                    # Convert to title case but preserve structure
                    v = v.title()
            data[k] = v

    return data



def parse_back_side_fields(text):
    data = {}
    raw = text or ""
    
    # Occupation - improved extraction
    occupation_patterns = [
        r'(?i)Occupation\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Occupation: Property Owner
        r'(?i)(?:Occupation|المهنة|Profession|الوظيفة)\s*[:\-]?\s*([^\n\r]{2,80})',
        r'(?i)Occupation\s*[:\-]?\s*([^\n\r]{1,60}?)(?:\n|Employer|Issuing|Family|$)',  # Stop at next field
    ]
    for pattern in occupation_patterns:
        m = re.search(pattern, raw)
        if m:
            occupation = m.group(1).strip()
            # Clean up common OCR artifacts but preserve spaces and capitalization
            occupation = re.sub(r'[^\w\s\-\.,]', '', occupation)  # Keep letters, numbers, spaces, hyphens, periods, commas
            # Remove leading/trailing special chars
            occupation = re.sub(r'^[\:\-\/\|]+|[\:\-\/\|]+$', '', occupation).strip()
            # Stop if we hit next field indicators
            occupation = re.split(r'(?i)\s+(?:Employer|Issuing|Family|صاحب)', occupation)[0].strip()
            # Filter out obvious OCR garbage (long number sequences, random characters)
            if not re.search(r'\d{6,}', occupation):  # Don't use if it has long number sequences
                if len(occupation) > 1 and len(occupation.split()) <= 5:  # Reasonable length
                    data['occupation'] = occupation
                    break
    
    # Employer - improved extraction
    employer_patterns = [
        r'(?i)Employer\s*[:\-]?\s*([A-Z][^\n\r]{1,80}?)(?:\n|Issuing|Family|$)',  # Employer: ... until next field
        r'(?i)(?:Employer|صاحب العمل|Company|الشركة|جهة العمل)\s*[:\-]?\s*([^\n\r]{2,80})',
        r'(?i)Employer\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z,]+)+)',  # Capitalized words pattern
    ]
    for pattern in employer_patterns:
        m = re.search(pattern, raw)
        if m:
            employer = m.group(1).strip()
            # Clean up but preserve commas and capitalization
            employer = re.sub(r'[^\w\s\-\.,]', '', employer)
            # Remove leading/trailing special chars
            employer = re.sub(r'^[\:\-\/\|]+|[\:\-\/\|]+$', '', employer).strip()
            # Stop if we hit next field
            employer = re.split(r'(?i)\s+(?:Issuing|Family|مكان)', employer)[0].strip()
            # Preserve commas in employer names (e.g., "Investors, Entrepreneurs, Specialized")
            if len(employer) > 1:
                data['employer'] = employer
                break
    
    # Issuing Place - improved extraction
    issuing_place_patterns = [
        r'(?i)Issuing Place\s*[:\-]?\s*([A-Z][a-z]+)',  # Issuing Place: Dubai
        r'(?i)(?:Issuing Place|مكان الإصدار|Place of Issue|جهة الإصدار)\s*[:\-]?\s*([^\n\r]{2,40})',
        r'(?i)Issuing Place\s*[:\-]?\s*([^\n\r]{1,40}?)(?:\n|If you find|Family|$)',  # Stop at next section
    ]
    for pattern in issuing_place_patterns:
        m = re.search(pattern, raw)
        if m:
            issuing_place = m.group(1).strip()
            # Clean up but preserve city names
            issuing_place = re.sub(r'[^\w\s\-\.,]', '', issuing_place)
            # Remove leading/trailing special chars
            issuing_place = re.sub(r'^[\:\-\/\|]+|[\:\-\/\|]+$', '', issuing_place).strip()
            # Stop if we hit next section
            issuing_place = re.split(r'(?i)\s+(?:If you find|Family|على هذه)', issuing_place)[0].strip()
            # Filter out common OCR errors
            if issuing_place.lower() not in ['file', 'number', 'num', 'no', 'yes']:
                if len(issuing_place) > 1 and len(issuing_place.split()) <= 3:  # City names are usually 1-3 words
                    data['issuing_place'] = issuing_place
                    break
    
    # Family Sponsor (Yes/No)
    family_sponsor_patterns = [
        r'(?i)(?:Family Sponsor|كفالة عائلية|Sponsor|كفالة|الکفالة)\s*[:\-]?\s*(Yes|No|نعم|لا|Y|N)',
        r'(?i)(?:Family Sponsor|كفالة عائلية|Sponsor|كفالة|الکفالة)[\s\S]{1,50}?(Yes|No|نعم|لا|Y|N)'
    ]
    for pattern in family_sponsor_patterns:
        m = re.search(pattern, raw)
        if m:
            value = m.group(1).strip().lower()
            if value in ['yes', 'y', 'نعم']:
                data['family_sponsor'] = 'Yes'
            elif value in ['no', 'n', 'لا']:
                data['family_sponsor'] = 'No'
            break
    
    return data



from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .ocr_space import ocr_space_file_multi_lang, ocr_space_pdf_all_pages
from .models import UAEDocumentVisa


def parse_uae_visa_fields(text: str):
    """
    Robust field parser for UAE Visa text.
    Refactored to handle file numbers, strict date validation, and cleaner name extraction.
    """
    data = {}
    if not text:
        return data

    raw = text
    # Normalize whitespace but keep newlines for line-based processing
    t = re.sub(r'[ \t]+', ' ', raw).replace('\r', '\n')

    def clean(v):
        if not v:
            return None
        v = v.strip()
        v = re.sub(r'^[\:\-\|\/\s]+', '', v)
        v = re.sub(r'[\s\|]+$', '', v)
        return v.strip()

    def validate_and_parse_date(date_str):
        if not date_str:
            return None
        # Normalize separators
        ds = date_str.replace('-', '/').replace('.', '/')
        parts = ds.split('/')
        if len(parts) != 3:
            return None
        
        y, m, d = None, None, None
        
        p0, p1, p2 = parts[0], parts[1], parts[2]
        
        # Try to detect format: YYYY/MM/DD or DD/MM/YYYY
        try:
            if len(p0) == 4:
                # YYYY/MM/DD
                y, m, d = int(p0), int(p1), int(p2)
            elif len(p2) == 4:
                # DD/MM/YYYY
                d, m, y = int(p0), int(p1), int(p2)
            else:
                return None
            
            # Strict Validation
            if not (1 <= m <= 12):
                return None
            if not (1 <= d <= 31):
                return None
            if not (1950 <= y <= 2100):
                return None

            # Return date object for logic/sorting
            from datetime import date
            return date(y, m, d)
        except ValueError:
            return None

    # ---------------- File Number ----------------
    # Pattern: 201/2013/3/43406 (3 or 4 parts)
    file_match = re.search(r'\b(\d{3,5}[/-]\d{4}[/-]\d{1,2}[/-]\d{4,8})\b', t)
    
    # Fallback for 3-part file number: 201/2024/3924425
    if not file_match:
        file_match = re.search(r'\b(\d{3,5}[/-]\d{4}[/-]\d{5,9})\b', t) 
    
    if file_match:
        data['file_number'] = clean(file_match.group(1))

    # ---------------- ID Number ----------------
    # 784-1980-1234567-1
    id_match = re.search(r'\b(784[/-]\d{4}[/-]\d{7}[/-]\d)\b', t)
    if not id_match:
         # Fallback: 784198012345671 (Unformatted 15 digits)
        id_match = re.search(r'\b(784\d{12})\b', t)

    if id_match:
        data['id_number'] = clean(id_match.group(1))

    # ---------------- UID No ----------------
    uid_match = re.search(r'(?i)(?:UID|Unified\s*Number|الرقم\s*الموحد)\s*[:\-]?\s*(\d{8,15})', t)
    if uid_match:
        data['uid_no'] = clean(uid_match.group(1))

    # ---------------- Passport Number ----------------
    # Strict regex: Must have at least one digit to avoid matching names like "ABHINAV"
    # Look for labeled passport number
    pass_match = re.search(r'(?i)(?:Passport\s*No|Passport\s*Number|رقم\s*الجواز)\s*[:\-]?\s*([A-Z0-9]*\d[A-Z0-9]*)', t)
    passport_val = None
    
    if pass_match:
        passport_val = clean(pass_match.group(1))
    
    # Fallback: look for common passport pattern (Letter + 6-9 digits) isolated
    if not passport_val:
        candidates = re.findall(r'\b([A-Z][0-9]{6,9})\b', t)
        if candidates:
            passport_val = candidates[0]
            
    # Fallback 2: Split passport number (e.g. "V79541 17") due to OCR spaces
    if not passport_val:
        # Match Letter, 5-8 digits, space, 1-3 digits. Total digits approx 6-9.
        split_match = re.search(r'\b([A-Z]\d{5,8})\s+(\d{1,3})\b', t)
        if split_match:
            # Recombine parts
            combined = split_match.group(1) + split_match.group(2)
            # Validation: Total length 7-12 chars
            if 7 <= len(combined) <= 12:
                passport_val = combined

    if passport_val:
        data['passport_no'] = passport_val

    # ---------------- Dates ----------------
    # Regex for dates: YYYY/MM/DD or DD/MM/YYYY
    date_pattern = r'\b(?:\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{4})\b'
    
    # We scan lines to associate dates with labels
    lines = t.splitlines()
    found_issue = False
    found_expiry = False

    for line in lines:
        line_clean = line.strip()
        # Issue Date
        if not found_issue and re.search(r'(?i)(Date\s*of\s*Issue|Issuing\s*Date|Issue\s*Date|تاريخ\s*الإصدار)', line_clean):
            # Look for date in this line or next line
            d_match = re.search(date_pattern, line_clean)
            if d_match:
                 vd = validate_and_parse_date(d_match.group(0))
                 if vd:
                     data['issuing_date'] = vd
                     found_issue = True

        # Expiry Date
        if not found_expiry and re.search(r'(?i)(Date\s*of\s*Expiry|Expiry\s*Date|Expires|Valid\s*Until|تاريخ\s*الانتهاء)', line_clean):
            d_match = re.search(date_pattern, line_clean)
            if d_match:
                vd = validate_and_parse_date(d_match.group(0))
                if vd:
                    data['expiry_date'] = vd
                    found_expiry = True

    # Fallback: Find all valid dates and heuristically assign
    if not found_issue or not found_expiry:
        all_dates_raw = re.findall(date_pattern, t)
        valid_dates = []
        for d in all_dates_raw:
            # Skip if this "date" is actually part of the file number we found
            if 'file_number' in data and data['file_number'] and d in data['file_number']:
                continue
            
            vd = validate_and_parse_date(d)
            if vd:
                valid_dates.append(vd)
        
        # Sort chronologically (date objects sort correctly)
        valid_dates.sort() 

        if valid_dates:
            # Usually DOB is oldest (if present), Issue is middle, Expiry is future
            
            if not found_issue and len(valid_dates) >= 1:
                # If expecting issue and expiry, assign earliest to issue, latest to expiry
                if len(valid_dates) >= 2:
                     if 'dob' not in data: 
                         data['issuing_date'] = valid_dates[0]
                         data['expiry_date'] = valid_dates[-1]

            if not found_expiry and valid_dates:
                data['expiry_date'] = valid_dates[-1] # Valid until is usually the latest date

    # Final Formatting: Convert date objects to DD-MMM-YYYY strings
    from datetime import date
    for k, v in data.items():
        if isinstance(v, date):
            data[k] = v.strftime("%d-%b-%Y")

    # ---------------- Name (Visa Holder) ----------------
    # Strategy: 
    # 1. Look for explicit Label "Name:" regex
    # 2. Look for large uppercase block not containing excluded keywords
    # 3. Support multi-line names (append next line if it looks like a name part)
    
    name_val = None
    
    # 1. Explicit Label
    name_label_match = re.search(r'(?i)(?:Name|Holder\'s\s*Name|الاسم)\s*[:\-]\s*([A-Z\s]{5,100})', t)
    if name_label_match:
        name_val = name_label_match.group(1)
    
    # 2. Heuristic: Find name block
    if not name_val:
        excluded = [
            'PASSPORT', 'UNITED', 'ARAB', 'EMIRATES', 'DUBAI', 'ABU', 'DHABI', 'VISA', 'RESIDENCE', 
            'PROFESSION', 'EMPLOYER', 'SPONSOR', 'SEX', 'MOI', 'MINISTRY', 'ACCOMPANID', 'ACCOMPANIED', 
            'PLACE', 'ISSUE', 'STUDENT', 'WORK', 'ALLOWED', 'FAMILY', 'HEAD', 'MANAGER', 'ENGINEER', 
            'DIRECTOR', 'PARTNER', 'INVESTOR', 'WIFE', 'HUSBAND', 'DAUGHTER', 'SON', 'HOUSE'
        ]
        
        # We need a robust way to iterate lines and find the specific block
        start_idx = -1
        
        # Clean lines tuple list: (original_index, clean_text)
        clean_lines = []
        for i, line in enumerate(lines):
            l = line.strip()
            if l:
                clean_lines.append((i, l))

        # Find the best starting line for the name
        best_cand_idx = -1
        max_score = 0

        for idx, (original_i, text) in enumerate(clean_lines):
            # aggressive filter: must be mostly uppercase, > 5 chars
            if len(text) < 3: continue
            
            words = text.split()
            # if len(words) < 1: continue 
            
            # Check if line contains numbers (Visa names usually don't have numbers)
            if re.search(r'\d', text): continue

            # Check for slashes (often in professions: Student/Not Allowed)
            if '/' in text: continue

            is_upper = True
            has_excluded = False
            
            # Check for excluded words
            for w in words:
                clean_w = re.sub(r'[^A-Z]', '', w.upper())
                if clean_w in excluded:
                    has_excluded = True
                    break
            
            if has_excluded: continue

            # Check casing (allow some OCR noise, but mostly upper)
            upper_chars = sum(1 for c in text if c.isupper())
            total_chars = len(text)
            if total_chars > 0 and (upper_chars / total_chars) < 0.5:
                 is_upper = False
            
            if is_upper:
                # Score candidates: Length + Position (prefer after Passport/Header)
                score = len(text)
                # Boost if previous line had "Passport" or "Accompanied"
                if idx > 0:
                    prev_text = clean_lines[idx-1][1].upper()
                    if 'PASSPORT' in prev_text or 'ACCOMPANIED' in prev_text:
                        score += 50
                
                if score > max_score:
                    max_score = score
                    best_cand_idx = idx

        if best_cand_idx != -1:
            # We found the start line. Now check next lines for continuation.
            final_name_parts = [clean_lines[best_cand_idx][1]]
            
            current_idx = best_cand_idx + 1
            while current_idx < len(clean_lines):
                next_text = clean_lines[current_idx][1]
                
                # Validation for next line:
                # 1. Must be Upper case
                # 2. No digits
                # 3. No excluded keywords (Profession, Box labels etc.)
                # 4. No special chars like / that imply profession
                
                # Check digits
                if re.search(r'\d', next_text): 
                    break
                
                # Check for slashes
                if '/' in next_text:
                    break

                # Check excluded
                has_keywords = False
                for w in next_text.split():
                    clean_w = re.sub(r'[^A-Z]', '', w.upper())
                    if clean_w in excluded:
                        has_keywords = True
                        break
                if has_keywords:
                    break

                # Check casing
                u_chars = sum(1 for c in next_text if c.isupper())
                t_chars = len(next_text)
                if t_chars > 0 and (u_chars / t_chars) < 0.5:
                    break # Likely Arabic or noise

                # It looks like a name part
                final_name_parts.append(next_text)
                current_idx += 1
            
            name_val = " ".join(final_name_parts)

    if name_val:
        # Final cleanup
        name_val = clean(name_val)
        # Store in employer_name as per legacy mapping
        data['employer_name'] = name_val
        data['full_name'] = name_val 

    return data



from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse

# @csrf_exempt
# @api_view(["POST"])
# @permission_classes([AllowAny])
# @api_view(['POST'])
# @authentication_classes([TokenAuthentication])
# @permission_classes([IsAuthenticated])


@api_view(['POST'])
@authentication_classes([])   # ⬅️ disable auth
@permission_classes([AllowAny])
def uae_visa_upload(request):
    """
    Handles UAE Visa uploads (image/pdf) using OCR.space API.
    """
    print(f"--- [VISA] Request Received ---")
    f = request.FILES.get('file')
    if not f:
        print(f"--- [VISA] Error: No file uploaded ---")
        return JsonResponse({"error": "No file uploaded"}, status=400)

    name = (f.name or "").lower()
    print(f"--- [VISA] File: {name} ({f.size} bytes) ---")
    is_pdf = name.endswith(".pdf") or (f.content_type == "application/pdf")

    # OCR process
    print(f"--- [VISA] Starting OCR processing (PDF: {is_pdf})... ---")
    if is_pdf:
        text, code, err = ocr_space_pdf_all_pages(f)
    else:
        text, code, err = ocr_space_file_multi_lang(f, False)

    if code != 0:
        print(f"--- [VISA] OCR Failed: {err} ---")
        return JsonResponse({"error": f"OCR failed: {err or 'unknown error'}"}, status=500)
    
    print(f"--- [VISA] OCR Success. Text length: {len(text)} chars ---")
    print(f"--- [VISA] Parsing fields... ---")

    fields = parse_uae_visa_fields(text or "")
    print(f"--- [VISA] Extracted Fields: {fields.keys()} ---")

    # Save record
    try:
        record = UAEDocumentVisa.objects.create(
            id_number=fields.get("id_number"),
            file_number=fields.get("file_number"),
            passport_no=fields.get("passport_no"),
            employer_name=fields.get("employer_name"),
            uid_no=fields.get("uid_no"),
            issuing_date=fields.get("issuing_date"),
            expiry_date=fields.get("expiry_date"),
            raw_text=text
        )
        print(f"--- [VISA] Record Saved: ID {record.id} ---")

        return JsonResponse({
            "ok": True,
            "record_id": record.id,
            "fields": {
                "id_number": record.id_number,
                "file_number": record.file_number,
                "passport_no": record.passport_no,
                "employer_name": record.employer_name,
                "full_name": fields.get("full_name"), # Explicitly return extracted full name
                "uid_no": record.uid_no,
                "issuing_date": record.issuing_date,
                "expiry_date": record.expiry_date,
            },
            "raw_text": record.raw_text[:2000]  # print trimmed full OCR result
        }, status=200)
    except Exception as e:
         print(f"--- [VISA] Failed to save record: {e} ---")
         return JsonResponse({"error": f"Database error: {str(e)}"}, status=500)

@api_view(['POST'])
@authentication_classes([])   # ⬅️ disable auth
@permission_classes([AllowAny])
def emirates_id_upload_test(request):
    """
    Global Emirates ID OCR test.
    Returns ONLY essential fields requested by the user.
    """
    from .ocr_space import ocr_space_file_multi_lang

    print(f"--- [EID] Request Received ---")
    files = request.FILES.getlist("file")
    if not files:
        print(f"--- [EID] Error: No files received ---")
        return JsonResponse({"error": "No files received"}, status=400)

    print(f"--- [EID] Processing {len(files)} files ---")
    combined_text = ""
    for i, file_obj in enumerate(files):
        print(f"--- [EID] Processing File {i+1}: {file_obj.name} ---")
        is_pdf = file_obj.name.lower().endswith(".pdf")
        text, code, err = ocr_space_file_multi_lang(file_obj, is_pdf)

        if code != 0:
            print(f"--- [EID] OCR Failed for {file_obj.name}: {err} ---")
            return JsonResponse({"error": f"OCR failed: {err}"}, status=500)
        
        print(f"--- [EID] OCR Success for {file_obj.name}. Length: {len(text)} ---")
        combined_text += " " + text

    # Extract data using your original logic
    print(f"--- [EID] Parsing fields... ---")
    front_fields = parse_fields(combined_text)
    
    try:
        back_fields = parse_back_side_fields(combined_text)
    except Exception as e:
        print(f"--- [EID] Warning: Back side parsing error: {e} ---")
        back_fields = {}

    merged = {**front_fields, **back_fields}
    print(f"--- [EID] Fields Extracted: {merged.keys()} ---")

    # FILTERED FINAL OUTPUT (Only fields you want)
    filtered = {
        "emirates_id": merged.get("emirates_id"),
        "name": merged.get("name"),
        "dob": merged.get("dob"),
        "expiry_date": merged.get("expiry_date"),
        "issuing_date": merged.get("issuing_date"),
        "nationality": merged.get("nationality"),
        "gender": merged.get("gender"),
        "occupation": merged.get("occupation"),
        "employer": merged.get("employer"),
        "issuing_place": merged.get("issuing_place"),
    }

    return JsonResponse({
        "ok": True,
        "fields": filtered,
    })
