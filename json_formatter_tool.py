from promptflow.core import tool

from chat_with_pdf.json_formatter import json_formatter


@tool
def json_formatter_tool(question: str, history: list):
    return json_formatter(question, history)
