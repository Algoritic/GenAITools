import os
import re
import faiss
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
from utils.index import FAISSIndex, SearchResultEntity
from utils.logging import log
from utils.oai import OAIEmbedding, render_with_token_limit
from data_masking import mask_sensitive_data

load_dotenv()

def read_masking_rules(file_path):
    rules = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if '->' in line:
                parts = line.split(' -> ')
                if len(parts) == 2:  # Ensure there are exactly two parts
                    pattern, replacement = parts
                    try:
                        # Add raw string handling for patterns
                        rules.append((re.compile(pattern), replacement))
                    except re.error:
                        # Skip malformed regex patterns silently
                        continue
    return rules

def mask_text(text, masking_rules):
    original_text = text
    for pattern, replacement in masking_rules:
        # Apply the masking rule to the text
        text = pattern.sub(replacement, text)
    if text != original_text:
        print(f"Masked Statement: {text}")
    return text

def find_context_from_cognitive_index(question: str, index_name: str | None = None):
    service_endpoint = os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"]
    key = os.environ["AZURE_SEARCH_API_KEY"]
    search_client = SearchClient(service_endpoint, index_name, AzureKeyCredential(key))

    # Perform the search query
    snippets = search_client.search(
        search_text=question,
        top=5,
        semantic_query=question,
        semantic_configuration_name="default",
        search_mode="any",
        query_answer_threshold=0.3,
        query_answer="extractive"
    )

    snippets = [dict((k, v) for k, v in x.items() if k == "content") for x in snippets]

    # Apply masking to snippets content
    masked_snippets = [mask_sensitive_data(snippet.get('content', '')) for snippet in snippets]
    print("Masked Text:", masked_snippets)

    snippets = [SearchResultEntity(content=x['content']) for x in snippets]

    # Load the prompt template
    template = Environment(
        loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__)))
    ).get_template("ea_qna_prompt.md")
    token_limit = int(os.environ.get("PROMPT_TOKEN_LIMIT", 2000))

    while True:
        try:
            prompt = render_with_token_limit(
                template,
                token_limit,
                question=question,
                context=enumerate(masked_snippets),
            )
            break
        except ValueError:
            masked_snippets = masked_snippets[:-1]
            snippets = snippets[:-1]
            log(f"Reducing snippet count to {len(snippets)} to fit token limit")

    return prompt, masked_snippets


def find_context(question: str, index_path: str):
    index = FAISSIndex(index=faiss.IndexFlatL2(1536), embedding=OAIEmbedding())
    index.load(path=index_path)
    search_results = index.query(question, top_k=5)

    masked_snippets = [mask_sensitive_data(result.text if hasattr(result, 'text') else str(result)) for result in search_results]
    print(f"Masked text: {masked_snippets}")
    
    template = Environment(
        loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__)))
    ).get_template("ea_qna_prompt.md")
    token_limit = int(os.getenv("PROMPT_TOKEN_LIMIT", 2000))

    while True:
        try:
            prompt = render_with_token_limit(
                template, token_limit, question=question, context=enumerate(masked_snippets)
            )
            break
        except ValueError:
            masked_snippets = masked_snippets[:-1]
            log(f"Reducing snippet count to {len(masked_snippets)} to fit token limit")

    return prompt, masked_snippets
