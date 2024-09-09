from typing import Dict, List
import PyPDF2
import faiss
import os

from pathlib import Path

from utils.oai import OAIEmbedding
from utils.index import FAISSIndex
from utils.logging import log
from utils.lock import acquire_lock
from constants import FILES_DIR, INDEX_DIR, PDF_DIR
from langchain_community.document_loaders import PyPDFLoader
import pymupdf
import pandas as pd
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    CorsOptions,
    ScoringProfile,
    SearchIndex,
    SearchFieldDataType,
    SimpleField,
    SearchField,
    SearchableField,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)
from azure.search.documents import SearchClient
import textwrap

from data_masking import mask_sensitive_data

def build_cognitive_index(index_name: str, pdf_paths: List[str]):
    create_cognitive_index(index_name)
    add_documents_to_cognitive_index(index_name, pdf_paths)
    return index_name

def add_documents_to_cognitive_index(index_name: str, pdf_paths: List[str]):
    service_endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
    index_name = "mbb-mss-ea-chatbot-final"  # os.environ["AZURE_SEARCH_INDEX_NAME"]
    key = os.environ["AZURE_SEARCH_API_KEY"]
    chunk_size = int(os.getenv("CHUNK_SIZE", 1024))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 128))
    credential = AzureKeyCredential(key)
    client = SearchClient(
        service_endpoint, credential=credential, index_name=index_name
    )

    documents: List[Dict] = []
    for pdf_path in pdf_paths:

        text = ""
        pdf = PyPDF2.PdfReader(pdf_path)
        for page in pdf.pages:
            text += page.extract_text()
        encoded_path = pdf_path.encode("utf-8")
        chunks = split_text(text, chunk_size, chunk_overlap)
        for i, chunk in enumerate(chunks):
            document = {
                "id": f"{encoded_path}_{i}".encode("utf-8"),  # Unique ID for each chunk
                "original_document_id": encoded_path,
                "chunk_number": i,
                "text": chunk,
            }
            documents.append(document)

    result = client.upload_documents(documents=documents)

    return result
    #return documents


def create_cognitive_index() -> str:
    service_endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
    index_name = "mbb-mss-ea-chatbot-final"  # os.environ["AZURE_SEARCH_INDEX_NAME"]
    key = os.environ["AZURE_SEARCH_API_KEY"]
    credential = AzureKeyCredential(key)

    client = SearchIndexClient(service_endpoint, credential=credential)
    # check if the index exist
    # if index_name in [index.name for index in client.list_indexes()]:
    # return index_name
    # delete the index
    # client.delete_index(index_name)

    cors_options = CorsOptions(allowed_origins=["*"], max_age_in_seconds=60)
    scoring_profiles: List[ScoringProfile] = []
    index = SearchIndex(
        fields=[
            SearchableField(
                name="text",
                type=SearchFieldDataType.String,
                search_analyzer="en.lucene",
            ),
            SearchField(name="id", type=SearchFieldDataType.String, key=True),
            SearchField(name="original_document_id", type=SearchFieldDataType.String),
            SearchField(name="chunk_number", type=SearchFieldDataType.Int32),
        ],
        name=index_name,
        scoring_profiles=scoring_profiles,
        cors_options=cors_options,
        semantic_search=SemanticSearch(
            configurations=[
                SemanticConfiguration(
                    name="default",
                    prioritized_fields=SemanticPrioritizedFields(
                        content_fields=[SemanticField(field_name="text")]
                    ),
                )
            ]
        ),
    )
    result = client.create_or_update_index(index)
    return index_name


def create_faiss_index(pdf_path: str) -> str:
    chunk_size = int(os.getenv("CHUNK_SIZE", 1024))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 128))
    log(f"Chunk size: {chunk_size}, chunk overlap: {chunk_overlap}")

    file_name = Path(pdf_path).name + f".index_{chunk_size}_{chunk_overlap}"
    index_persistent_path = Path(INDEX_DIR) / file_name
    index_persistent_path = index_persistent_path.resolve().as_posix()
    lock_path = index_persistent_path + ".lock"
    log("Index path: " + os.path.abspath(index_persistent_path))

    with acquire_lock(lock_path):
        if os.path.exists(os.path.join(index_persistent_path, "index.faiss")):
            log("Index already exists, bypassing index creation")
            return index_persistent_path
        else:
            if not os.path.exists(index_persistent_path):
                os.makedirs(index_persistent_path)

        log("Building index")
        # pdf_reader = PyPDF2.PdfReader(pdf_path)

        # text = ""
        # for page in pdf_reader.pages:
        #     text += page.extract_text()

        # loader = PyPDFLoader(pdf_path)
        # pages = loader.load()
        # for page in pages:
        #     text += page.page_content
        pdf_reader = PyPDF2.PdfReader(pdf_path)

        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        # Mask sensitive data in the extracted text before chunking and indexing
        text = mask_sensitive_data(text)

        df = pd.read_excel(os.path.join(FILES_DIR, "Dynamo Components.xlsx"))
        md_table = df.to_markdown(index=False)

        # doc = pymupdf.open(pdf_path)  # open a document
        # for page in doc:  # iterate the document pages
        #     text += page.get_text()  # get plain text encoded as UTF-8

        # Chunk the words into segments of X words with Y-word overlap, X=CHUNK_SIZE, Y=OVERLAP_SIZE
        #segments = split_text(md_table, chunk_size, chunk_overlap)
        segments = split_text(text, chunk_size, chunk_overlap)
        
        log(f"Number of segments: {len(segments)}")

        index = FAISSIndex(index=faiss.IndexFlatL2(1536), embedding=OAIEmbedding())
        index.insert_batch(segments)

        index.save(index_persistent_path)

        log("Index built: " + index_persistent_path)
        return index_persistent_path


# Split the text into chunks with CHUNK_SIZE and CHUNK_OVERLAP as character count
def split_text(text, chunk_size, chunk_overlap):
    # Calculate the number of chunks
    num_chunks = (len(text) - chunk_overlap) // (chunk_size - chunk_overlap)

    # Split the text into chunks
    chunks = []
    for i in range(num_chunks):
        start = i * (chunk_size - chunk_overlap)
        end = start + chunk_size
        chunks.append(text[start:end])

    # Add the last chunk
    chunks.append(text[num_chunks * (chunk_size - chunk_overlap) :])

    return chunks
