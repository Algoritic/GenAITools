from promptflow.connections import CustomStrongTypeConnection
from promptflow.contracts.types import Secret


class MultiConnection(CustomStrongTypeConnection):
    """Custom strong type connection.

    :param api_key: The api key.
    :type api_key: Secret
    :param api_base: The api base.
    :type api_base: String
    """

    api_key: Secret
    api_base: str
    api_version: str

    embedding_model_deployment_name: str
    chat_model_deployment_name: str

    azure_storage_connection_string: Secret
    azure_container_name: str

    azure_search_api_key: Secret
    azure_search_service_endpoint: str
