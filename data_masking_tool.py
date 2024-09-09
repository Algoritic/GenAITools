from promptflow.core import tool
from chat_with_pdf.data_masking import mask_sensitive_data

from promptflow.core import tool

@tool
def data_masking_tool(text: str) -> dict:
    masked_text = mask_sensitive_data(text)
    print(f"Masked Text: {masked_text}", flush=True)
    return {"masked_text": masked_text}


# @tool
# def data_masking_tool(text: str):
#     print(f"Received text: {text}")
#     masked_text = mask_sensitive_data(text)
#     print(f"Masked text: {masked_text}")
    
#     if masked_text is None:
#         raise ValueError("Masked text is None.")
    
#     result = {"masked_text": masked_text}
#     print(f"Returning result: {result}")
#     return result