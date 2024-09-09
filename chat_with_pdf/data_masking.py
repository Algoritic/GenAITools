import re
from promptflow.core import tool
@tool
def mask_sensitive_data(text: str) -> str:
    # Define masking rules with updated regex patterns
    patterns = {
        # IC Number: Keep the initial number and mask the rest
        r'(\d)\d{11}': r'\1XXXXXXXXXX',
        
        # Phone Number: Various formats
        r'(?:\+\d{2} \d{1,2}-\d{3,4} \d{4}|\d{2}-\d{8}|\+\d{2}-\d{2}-\d{7,8}|\d{2}-\d{4}-\d{4}|\d{3}-\d{3}-\d{4}|\d{9,10})': '01XXXXXXXXX',
        
        # Passport Number
        r'[A-Z]\d{8}': 'AXXXXXXXX',
        
        # Driver’s License Number
        r'[A-Z]\d{12}': 'AXXXXXXXXXXX',
        
        # Email Address
        r'[\w._%+-]+@[\w.-]+\.[a-zA-Z]{2,}': 'XXXX@XXXX.XXX',
        
        # Bank Account Number
        r'\d{12}': 'XXXXXXXXXXXX',
        
        # Credit Card Number
        r'\d{4}-\d{4}-\d{4}-\d{4}': '1234-XXXX-XXXX-3456',
        
        # Medical Record Number
        r'MRN\d{6}': 'MRNXXXXXX',
        
        # Residential Address: Mask the street number and postal code
        r'\d{3} \w+ \d{5}, \d{4} \w+': '123 XXXX, XXXX Kuala Lumpur',
        
        # NRIC Number (for non-Malaysian citizens)
        r'[A-Z]\d{7}[A-Z]': 'AXXXXXXX',
        
        # Tax Identification Number (TIN)
        r'T\d{12}': 'TXXXXXXXXXXX',
    }
    masked_text = text
    for pattern, replacement in patterns.items():
        masked_text = re.sub(pattern, replacement, masked_text)
    
    return masked_text