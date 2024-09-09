from promptflow.core import tool
from chat_with_pdf.qna import qna

# @tool
# def qna_tool(prompt: str, history: list):
#     print(f"Received prompt: {prompt}")
#     stream = qna(prompt, convert_chat_history_to_chatml_messages(history))

#     answer = ""
#     for str in stream:
#         answer = answer + str + ""

#     return {"answer": answer}

# def convert_chat_history_to_chatml_messages(history):
#     messages = []
#     for item in history:
#         messages.append({"role": "user", "content": item["inputs"]["question"]})
#         messages.append({"role": "assistant", "content": item["outputs"]["answer"]})

#     return messages


@tool
def qna_tool(prompt: str, history: list):
    try:
        print(f"Received prompt: {prompt}")

        # Convert chat history to ChatML messages
        chat_history = convert_chat_history_to_chatml_messages(history)

        # Process the prompt with the chat history
        stream = qna(prompt, chat_history)

        # Collect the answer from the stream
        answer = ""
        for chunk in stream:
            answer += chunk

        return answer

    except Exception as e:
        print(f"Error occurred in qna_tool: {e}")
        return {"answer": "An error occurred while processing the request."}


def convert_chat_history_to_chatml_messages(history):
    messages = []
    for item in history:
        # Extract user and assistant messages with validation
        user_message = item.get("inputs", {}).get("question", "")
        assistant_message = item.get("outputs", {}).get("answer", "")

        if user_message:
            messages.append({"role": "user", "content": user_message})
        if assistant_message:
            messages.append({
                "role": "assistant",
                "content": assistant_message
            })

    return messages
