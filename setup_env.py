import os
from typing import Union

from promptflow.connections import (
    AzureOpenAIConnection,
    CustomConnection,
    OpenAIConnection,
)
from promptflow.core import tool

from chat_with_pdf.connections.multi_connection import MultiConnection
from chat_with_pdf.utils.lock import acquire_lock

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) + "/chat_with_pdf/"


@tool
def setup_env(
    connection: Union[AzureOpenAIConnection, OpenAIConnection, MultiConnection],
    config: dict,
):
    if not connection or not config:
        return

    if isinstance(connection, AzureOpenAIConnection):
        os.environ["OPENAI_API_TYPE"] = "azure"
        os.environ["OPENAI_API_BASE"] = connection.api_base
        os.environ["OPENAI_API_KEY"] = connection.api_key
        os.environ["OPENAI_API_VERSION"] = connection.api_version

    if isinstance(connection, OpenAIConnection):
        os.environ["OPENAI_API_KEY"] = connection.api_key
        if connection.organization is not None:
            os.environ["OPENAI_ORG_ID"] = connection.organization

    # if isinstance(connection, MultiConnection):
    #     os.environ["OPENAI_API_TYPE"] = "azure"
    #     os.environ["OPENAI_API_BASE"] = connection.api_base
    #     os.environ["OPENAI_API_KEY"] = connection.secrets["api_key"]
    #     os.environ["OPENAI_API_VERSION"] = connection.api_version

    #     os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"] = (
    #         connection.azure_search_service_endpoint
    #     )
    #     os.environ["AZURE_SEARCH_API_KEY"] = connection.secrets["azure_search_api_key"]
    #     os.environ["AZURE_CONTAINER_NAME"] = connection.azure_container_name
    #     os.environ["AZURE_STORAGE_CONNECTION_STRING"] = connection.secrets[
    #         "azure_storage_connection_string"
    #     ]

    if isinstance(connection, MultiConnection):
        os.environ["OPENAI_API_TYPE"] = "azure"
        os.environ["OPENAI_API_BASE"] = connection.api_base
        os.environ["OPENAI_API_KEY"] = connection.secrets["api_key"]
        os.environ["OPENAI_API_VERSION"] = connection.api_version

        os.environ["AZURE_SEARCH_SERVICE_ENDPOINT"] = (
            connection.azure_search_service_endpoint
        )
        os.environ["AZURE_SEARCH_API_KEY"] = connection.secrets["azure_search_api_key"]
        if "azure_container_name" in connection.configs:
            os.environ["AZURE_CONTAINER_NAME"] = connection.configs["azure_container_name"]
        else:
            raise KeyError("The 'azure_container_name' key is missing in the connection configuration.")
        os.environ["AZURE_STORAGE_CONNECTION_STRING"] = connection.secrets[
            "azure_storage_connection_string"
        ]

    for key in config:
        os.environ[key] = str(config[key])

    with acquire_lock(BASE_DIR + "create_folder.lock"):
        if not os.path.exists(BASE_DIR + ".pdfs"):
            os.mkdir(BASE_DIR + ".pdfs")
        if not os.path.exists(BASE_DIR + ".index/.pdfs"):
            os.makedirs(BASE_DIR + ".index/.pdfs")

    return "Ready"
