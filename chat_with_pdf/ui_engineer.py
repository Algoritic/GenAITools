import os

from dotenv import load_dotenv
from promptflow.core import Prompty


def get_component_list(question: str):
    if "AZURE_OPENAI_API_KEY" not in os.environ:
        # load environment variables from .env file
        load_dotenv()
    print(os.environ)
    root_path = os.path.dirname(os.path.abspath(__file__))
    prompty_path = os.path.join(root_path, "ui_engineer.prompty")
    f = Prompty.load(prompty_path)
    answer = f(question=question)
    print({"ui_engineer: ": answer})
    return answer
