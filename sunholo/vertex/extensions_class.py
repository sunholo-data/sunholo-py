try:
    from vertexai.preview import extensions
except ImportError:
    extensions = None

from .init import init_vertex
from ..logging import log
from ..utils.gcp_project import get_gcp_project
from ..utils.parsers import validate_extension_id
import base64
import json
from io import StringIO

class VertexAIExtensions:
    def __init__(self):
        if extensions is None:
            raise ImportError("VertexAIExtensions needs vertexai.previewextensions to be installed. Install via `pip install sunholo[gcp]`")
        
        self.CODE_INTERPRETER_WRITTEN_FILES = []
        self.css_styles = """
        <style>
        .main_summary {
          font-weight: bold;
          font-size: 14px; color: #4285F4;
          background-color:rgba(221, 221, 221, 0.5); padding:8px;}
        </style>
        """
        self.IMAGE_FILE_EXTENSIONS = set(["jpg", "jpeg", "png"])
        self.location = "us-central1"

    def list_extensions(self):
        the_list = extensions.Extension.list()
        
        extensions_list = []
        for ext in the_list:
            extensions_list.append({
                "resource_name": getattr(ext, 'resource_name', ''),
                "display_name": getattr(ext, 'display_name', 'N/A'),
                "description": getattr(ext, 'description', 'N/A')
            })
        
        return extensions_list
        

    def get_extension_import_config(self, display_name: str, description: str,
                                    api_spec_gcs: dict, service_account_name: dict, tool_use_examples: list):
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
            "displayName": display_name,
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

    def create_extension_instance(self, display_name: str, description: str, open_api_gcs_uri: str,
                                  llm_name: str = None, llm_description: str = None, runtime_config: dict = None, service_account: str = None):
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

    def execute_extension(self, operation_id: str, operation_params: dict, extension_id: str):
        init_vertex(location=self.location)

        if not extension_id.startswith("projects/"):
            project_id = get_gcp_project()
            extension_name = f"projects/{project_id}/locations/{self.location}/extensions/{extension_id}"
        else:
            extension_name = extension_id

        extension = extensions.Extension(extension_name)

        response = extension.execute(
            operation_id=operation_id,
            operation_params=operation_params,
        )

        return response

    def execute_code_extension(self, 
                               query: str, 
                               filenames: list[str] = None, 
                               gcs_files: list[str] = None,
                               bucket_name: str = None):
        if filenames and gcs_files:
            raise ValueError("Can't specify both filenames and gcs_files")
        
        listed_extensions = self.list_extensions()
        code_interpreter_exists = False
        for ext in listed_extensions:
            if ext.get('display_name') == 'Code Interpreter':
                code_interpreter_exists = True
                extension_code_interpreter = extensions.Extension(ext['resource_name'])
                break

        if not code_interpreter_exists:
            if bucket_name:
                runtime_config = {
                    "codeInterpreterRuntimeConfig": {
                        "fileInputGcsBucket": bucket_name,
                        "fileOutputGcsBucket": bucket_name,
                    }
                }
                log.info(f"Creating buckets with {runtime_config=}")
            else:
                runtime_config = {}

            extension_code_interpreter = extensions.Extension.from_hub("code_interpreter", runtime_config=runtime_config)

        # This field is only applicable when `file_output_gcs_bucket` is specified in `Extension.CodeInterpreterRuntimeConfig`.

        log.info(f"extension_code_interpreter: {extension_code_interpreter.resource_name}")
        operation_params = {"query": query}

        file_arr = None
        if filenames:
            file_arr = [
                {
                    "name": filename,
                    "contents": base64.b64encode(open(filename, "rb").read()).decode()
                }
                for filename in filenames
            ]
            operation_params["files"] = file_arr
        
        if gcs_files:
            operation_params["file_gcs_uris"] = gcs_files
        log.info(f"Executing code interpreter with {operation_params=}")
        response = extension_code_interpreter.execute(
            operation_id="generate_and_execute",
            operation_params=operation_params)

        if response.get('execution_error'):
            #TODO: setup iteration many times with a timeout
            log.error(f"Code Execution Response failed with: {response.get('execution_error')} - maybe retry?")
            new_query = f"""
<original_query>{query}</original_query>
<original_output>{response.get('generated_code')}</original_output>
The code above failed with this error:
<code_error>{response.get('execution_error')}</code_error>
Please try again again to satisfy the original query.
"""
            operation_params = {"query": new_query}
            response = extension_code_interpreter.execute(
                operation_id="generate_and_execute",
                operation_params=operation_params)
            
            if response.get('execution_error'):
                log.error(f"Code Execution Response failed twice: {response.get('execution_error')}")

        if 'output_files' in response:
            self.CODE_INTERPRETER_WRITTEN_FILES.extend(
                [item['name'] for item in response['output_files']])
        
        if 'output_gcs_uris' in response:
            self.CODE_INTERPRETER_WRITTEN_FILES.extend(response['output_gcs_uris'])   

        return response

    def parse_files_to_html(self, outputFiles, save_files_locally=True):
        file_list = []
        details_tml = """<details><summary>{name}</summary><div>{html_content}</div></details>"""

        if not outputFiles:
            return "No Files generated from the code"
        # Sort output_files so images are displayed before other files such as JSON.
        for output_file in sorted(
                outputFiles,
                key=lambda x: x["name"].split(".")[-1] not in self.IMAGE_FILE_EXTENSIONS,
        ):
            file_name = output_file.get("name")
            file_contents = base64.b64decode(output_file.get("contents"))
            if save_files_locally:
                open(file_name, "wb").write(file_contents)

            if file_name.split(".")[-1] in self.IMAGE_FILE_EXTENSIONS:
                # Render Image
                file_html_content = ('<img src="data:image/png;base64, '
                                     f'{output_file.get("contents")}" />')
            elif file_name.endswith(".json"):
                import pprint
                # Pretty print JSON
                json_pp = pprint.pformat(
                    json.loads(file_contents.decode()),
                    compact=False,
                    width=160)
                file_html_content = (f'<span>{json_pp}</span>')
            elif file_name.endswith(".csv"):
                # CSV
                try:
                    import pandas
                except ImportError:
                    log.error("Need pandas for csv processing")
                csv_md = pandas.read_csv(
                    StringIO(file_contents.decode())).to_markdown(index=False)
                file_html_content = f'<span>{csv_md}</span>'
            elif file_name.endswith(".pkl"):
                # PKL
                file_html_content = f'<span>Preview N/A</span>'
            else:
                file_html_content = f"<span>{file_contents.decode()}</span>"

            file_list.append({'name': file_name, "html_content": file_html_content})

        buffer_html = [details_tml.format(**_file) for _file in file_list]
        return "".join(buffer_html)
    
    def process_response(self, response: dict, save_file_name=None) -> str:
        result_template = """
        <details open>
            <summary class='main_summary'>{summary}:</summary>
            <div><pre>{content}</pre></div>
        </details>
        """

        result = ""
        code = response.get('generated_code')
        if 'execution_result' in response and response['execution_result'] != "":
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
            content=self.parse_files_to_html(
                response.get('output_files', []),
                save_files_locally=True))

        html_content = f"""
{self.css_styles}
<div id='main'>
    <h3>Generated Code by Code Interpreter</h3>
    <pre><code>{code}</code></pre>
    <h3>Code Execution Results</h3>
    {result}
</div>
"""
        if save_file_name:
            with open(save_file_name or 'code_execution_results.html', 'w') as file:
                file.write(html_content)

        return html_content