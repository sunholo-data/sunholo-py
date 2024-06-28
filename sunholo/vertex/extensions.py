# https://cloud.google.com/vertex-ai/generative-ai/docs/extensions/create-extension
# https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/extension#python
from vertexai.preview import extensions
from .init import init_vertex
from ..logging import log
from ..utils.gcp_project import get_gcp_project
from ..utils.parsers import validate_extension_id

def get_extension_import_config(
        display_name: str, 
        description: str,
        api_spec_gcs: dict,
        service_account_name: dict,
        tool_use_examples: list):

    tool_use_examples = [
        {
            "extensionOperation": {
                "operationId": "say_hello",
            },
            "displayName": "Say hello in the requested language",
            "query": "Say hello in French",
            "requestParams": {
                "fields": [
                {
                    "key": "apiServicePrompt",
                    "value": {
                    "string_value": "French",
                    }
                }
                ]
            },
            "responseParams": {
                "fields": [
                {
                    "key": "apiServiceOutput",
                    "value": {
                    "string_value": "bonjour",
                    },
                }
                ],
            },
            "responseSummary": "Bonjour"
            }
    ]

    
    return {
        "displayName":  display_name,
        "description": description,
        "manifest": {
            "name": "EXTENSION_NAME_LLM",
            "description": "DESCRIPTION_LLM",
            "apiSpec": {
                "openApiGcsUri": api_spec_gcs,
            },
            "authConfig": {
                "authType": "OAUTH",
                "oauthConfig": {"service_account": service_account_name}
            }
        },
        "toolUseExamples": tool_use_examples, 
        }

# once an extension is available, call it in code here
def create_extension_instance(
        display_name: str,
        description: str,
        open_api_gcs_uri: str,
        llm_name: str=None,
        llm_description: str=None,
        runtime_config: dict=None,
        service_account: str=None,
):
    """
    Args:
    - display_name: for the human. parsed to be used as extension_name
    - description: for the human
    - open_api_gcs_uri: location on GCS where open_ai yaml spec is
    - llm_name: for the model.  If None, uses display_name
    - llm_description: for the model.  If None, uses description
    - service_account: If not specified, the Vertex AI Extension Service Agent is used to execute the extension.
    
    """
    project_id = get_gcp_project()
    extension_name = f"projects/{project_id}/locations/us-central1/extensions/{validate_extension_id(display_name)}"

    extension = extensions.Extension.create(
        extension_name=extension_name,
        display_name=display_name,
        description=description,
        runtime_config=runtime_config or None,
        manifest={
            "name": llm_name or display_name,
            "description": llm_description or description,
            "api_spec": {
                "open_api_gcs_uri": open_api_gcs_uri
            },
            "auth_config": {
                "auth_type": "GOOGLE_SERVICE_ACCOUNT_AUTH",
                "google_service_account_config": service_account or {},
            },
        },
    )
    log.info(f"Creating Vertex Extension: {extension=}")

    return extension



def create_extension_code_interpreter(
        code_artifacts_bucket=None
):

    # only us-central for now
    location = "us-central1"
    init_vertex(location=location)

    runtime_config=None
    if code_artifacts_bucket:
        runtime_config = {"codeInterpreterRuntimeConfig": 
                            {
                                "fileInputGcsBucket": code_artifacts_bucket,
                                "fileOutputGcsBucket": code_artifacts_bucket
                            }
                        }

    code_extension = create_extension_instance(
        display_name="Code Interpreter",
        description="This extension generates and executes code in the specified language",
        open_api_gcs_uri="gs://vertex-extension-public/code_interpreter.yaml",
        llm_name="code_interpreter_tool",
        llm_description="Google Code Interpreter Extension",
        runtime_config=runtime_config
        )
    log.info(f"Created code extension: {code_extension=}")

    return code_extension
