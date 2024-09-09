from promptflow.core import tool

from chat_with_pdf.ui_engineer import get_component_list as ui_engineer


@tool
def get_component_list(question: str, env_ready_signal: str):
    return ui_engineer(question)
