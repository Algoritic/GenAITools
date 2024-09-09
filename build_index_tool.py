from promptflow.core import tool

from chat_with_pdf.build_index import build_cognitive_index


@tool
def build_index_tool(pdf_path: str, index_name: str) -> str:
    return build_cognitive_index(index_name=index_name, pdf_paths=[pdf_path])
