from promptflow.core import tool

from chat_with_pdf.connections.multi_connection import MultiConnection
from chat_with_pdf.find_context import find_context, find_context_from_cognitive_index

# @tool
# def find_context_tool(question: str, index_path: str, env_ready_signal: str):
#     prompt, context = find_context_from_cognitive_index(question, index_path)

#     return {"prompt": prompt, "context": [c.content for c in context]}

@tool
def find_context_tool(question: str, index_path: str, env_ready_signal: str):
    prompt, context = find_context_from_cognitive_index(question, index_path)

    if isinstance(context, list) and all(isinstance(c, str) for c in context):
        return {"prompt": prompt, "context": context}
    else:
        raise TypeError("Expected 'context' to be a list of strings")
