import argparse
import os

from azure.storage.blob import BlobServiceClient
from build_index import (
    add_documents_to_cognitive_index,
    create_cognitive_index,
    create_faiss_index
)
from constants import INDEX_DIR, PDF_DIR
from dotenv import load_dotenv
from download import download, fetch_pdfs_from_blob
from find_context import find_context, find_context_from_cognitive_index
from qna import qna
from rewrite_question import rewrite_question
from utils.lock import acquire_lock
from utils.index import FAISSIndex
from data_masking import mask_sensitive_data

def chat_with_pdf(question: str, pdf_url: str, history: list):
    AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
    blob_service_client = BlobServiceClient.from_connection_string(
        AZURE_STORAGE_CONNECTION_STRING
    )
    container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)
    # Mask sensitive data in user input
    masked_question = mask_sensitive_data(question)
    print(f"Masked Question: {masked_question}", flush=True) # Verifying statement
    with acquire_lock("create_folder.lock"):
        if not os.path.exists(PDF_DIR):
            os.mkdir(PDF_DIR)
        if not os.path.exists(INDEX_DIR):
            os.makedirs(INDEX_DIR)
    #pdf_paths = fetch_pdfs_from_blob(container_client)
    # index_name = create_cognitive_index()
    # add_documents_to_cognitive_index(index_name, pdf_paths)

    #pdf_path = download(pdf_url)
    # index_path = create_faiss_index(pdf_path)
    # q = rewrite_question(question, history)
    # prompt, context = find_context(question, index_path)
    # q = rewrite_question(masked_question, history)
    prompt, context = find_context_from_cognitive_index(masked_question)
    stream = qna(prompt, history)

    return stream, context

def print_stream_and_return_full_answer(stream):
    answer = ""
    for str in stream:
        print(str, end="", flush=True)
        answer = answer + str + ""
    print(flush=True)

    return answer


def main_loop(url: str):
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

    history = []
    while True:
        question = input("\033[92m" + "$User (type q! to quit): " + "\033[0m")
        if question == "q!":
            break

        stream, context = chat_with_pdf(question, url, history)

        print("\033[92m" + "$Bot: " + "\033[0m", end=" ", flush=True)
        answer = print_stream_and_return_full_answer(stream)
        history = history + [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]


def main():
    parser = argparse.ArgumentParser(description="Ask questions about a PDF file")
    parser.add_argument("url", help="URL to the PDF file")
    args = parser.parse_args()

    main_loop(args.url)


if __name__ == "__main__":
    main()
