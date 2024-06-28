# https://cloud.google.com/vertex-ai/generative-ai/docs/extensions/create-extension
# https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/extension#python
from vertexai.preview import extensions
from .init import init_vertex
from ..logging import log
from ..utils.gcp_project import get_gcp_project
from ..utils.parsers import validate_extension_id

# https://github.com/GoogleCloudPlatform/applied-ai-engineering-samples/blob/main/genai-on-vertex-ai/vertex_ai_extensions/notebooks/pandas_code_interpreter.ipynb
import base64
import json
import pprint
import pandas
from io import StringIO

global CODE_INTERPRETER_WRITTEN_FILES
CODE_INTERPRETER_WRITTEN_FILES = []

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
    log.info(f"Created Vertex Extension: {extension_name}")

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

    llm_description="""
Tool to generate and execute valid Python code from a natural
  language description, or to execute custom Python code.
  Use this tool to:
  - generate and/or execute code for various tasks:
    - perform a wide variety of mathematical calculations, for example, add,
      subtract, multiply, divide, average, power, factorial, quotient,
      formulae, logarithms, random numbers, trigonometric functions, and
      equations;
    - sort, filter, select top results, and otherwise analyze data (including
      data acquired from other tools and Extensions);
    - create visualizations, plot charts, draw graphs, shapes, print results,
      etc.
  - execute custom code and get results and output files.
"""

    code_extension = create_extension_instance(
        display_name="Code Interpreter",
        description="This extension generates and executes code in the specified language",
        open_api_gcs_uri="gs://vertex-extension-public/code_interpreter.yaml",
        llm_name="code_interpreter_tool",
        llm_description=llm_description,
        runtime_config=runtime_config
        )
    log.info(f"Created code extension: {code_extension=}")

    return code_extension

def execute_extension(operation_id: str,
                      operation_params: dict,
                      extension_id: str):

    # only us-central for now
    location = "us-central1"
    init_vertex(location=location)

    if not extension_id.startswith("projects/"):
        project_id=get_gcp_project()
        extension_name = f"projects/{project_id}/locations/{location}/extensions/{extension_id}"
    else:
        extension_name=extension_id
    
    extension = extensions.Extension(extension_name)

    response = extension.execute(
        operation_id=operation_id,
        # {"query": "find the max value in the list: [1,2,3,4,-5]"}
        operation_params=operation_params,
    )

    return response

def execute_code_extension(query:str, filenames: list[str]=None, gcs_files: list[str]=None):

    if filenames and gcs_files:
        raise ValueError("Can't specify both filenames and gcs_files")
    
    extension_code_interpreter = extensions.Extension.from_hub("code_interpreter")

    file_arr=None
    if filenames:
        file_arr = [
            {
                "name": filename,
                "contents":  base64.b64encode(open(filename, "rb").read()).decode()
            }
            for filename in filenames
        ]

    response = extension_code_interpreter.execute(
        operation_id = "generate_and_execute",
        operation_params={
            "query": query,
            "files": file_arr,
            "file_gcs_uris": gcs_files
        })
    
    CODE_INTERPRETER_WRITTEN_FILES.extend(
        [item['name'] for item in response['output_files']])

    if response.get('execution_error'):
        log.error(f"Code Execution Response failed with: {response.get('execution_error')} - maybe retry?")
    
    return response

css_styles = """
<style>
.main_summary {
  font-weight: bold;
  font-size: 14px; color: #4285F4;
  background-color:rgba(221, 221, 221, 0.5); padding:8px;}
</style>
        """

# Parser to visualise the content of returned files as HTML.
def parse_files_to_html(outputFiles, save_files_locally = True):
    IMAGE_FILE_EXTENSIONS = set(["jpg", "jpeg", "png"])
    file_list = []
    details_tml = """<details><summary>{name}</summary><div>{html_content}</div></details>"""

    if not outputFiles:
      return "No Files generated from the code"
    # Sort output_files so images are displayed before other files such as JSON.
    for output_file in sorted(
        outputFiles,
        key=lambda x: x["name"].split(".")[-1] not in IMAGE_FILE_EXTENSIONS,
    ):
        file_name = output_file.get("name")
        file_contents = base64.b64decode(output_file.get("contents"))
        if save_files_locally:
          open(file_name,"wb").write(file_contents)

        if file_name.split(".")[-1] in IMAGE_FILE_EXTENSIONS:
            # Render Image
            file_html_content = ('<img src="data:image/png;base64, '
                                f'{output_file.get("contents")}" />')
        elif file_name.endswith(".json"):
            # Pretty print JSON
            json_pp = pprint.pformat(
                        json.loads(file_contents.decode()),
                        compact=False,
                        width=160)
            file_html_content =  (f'<span>{json_pp}</span>')
        elif file_name.endswith(".csv"):
            # CSV
            csv_md = pandas.read_csv(
                  StringIO(file_contents.decode())).to_markdown(index=False)
            file_html_content = f'<span>{csv_md}</span>'
        elif file_name.endswith(".pkl"):
            # PKL
            file_html_content = f'<span>Preview N/A</span>'
        else:
            file_html_content = f"<span>{file_contents.decode()}</span>"

        file_list.append({'name': file_name, "html_content": file_html_content})

    buffer_html = [ details_tml.format(**_file) for _file in file_list ]
    return "".join(buffer_html)

# Processing code interpreter response to html visualization.
def process_response(response: dict, save_files_locally = None) -> None:

    result_template = """
    <details open>
        <summary class='main_summary'>{summary}:</summary>
        <div><pre>{content}</pre></div>
    </details>
    """

    result = ""
    code = response.get('generated_code')
    if 'execution_result' in response and response['execution_result']!="":
        result = result_template.format(
            summary="Executed Code Output",
            content=response.get('execution_result'))
    else:
        result = result_template.format(
        summary="Executed Code Output",
        content="Code does not produce printable output.")

    if response.get('execution_error', None):
        result += result_template.format(
            summary="Generated Code Raised a (Possibly Non-Fatal) Exception",
            content=response.get('execution_error', None))

    result += result_template.format(
        summary="Files Created <u>(Click on filename to view content)</u>",
        content=parse_files_to_html(
            response.get('output_files', []),
            save_files_locally = True))

    html_content = f"""
{css_styles}
<div id='main'>
    <div id="right">
      <h3>Generated Code by Code Interpreter</h3>
      <pre><code>{code}</code></pre>
    </div>
    <div id="left">
      <h3>Code Execution Results</h3>
      {result}
    </div>
</div>
"""
    if save_files_locally:
        # write to local file
        pass
  
    return html_content
