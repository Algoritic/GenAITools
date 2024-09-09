import os

from utils.oai import OAIChat


def qna(prompt: str, history: list):
    max_completion_tokens = int(os.environ.get("MAX_COMPLETION_TOKENS"))
    temperature = float(os.environ.get("TEMPERATURE"))

    chat = OAIChat()
    stream = chat.stream(
        messages=history + [{"role": "user", "content": prompt}],
        max_tokens=max_completion_tokens,
        temperature=temperature,
    )

    return stream
