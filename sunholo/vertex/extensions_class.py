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
import os

class VertexAIExtensions:
    """
    Example

    ```python
    from sunholo.vertex import VertexAIExtensions
    vex = VertexAIExtensions()
    vex.list_extensions()
    # [{'resource_name': 'projects/374404277595/locations/us-central1/extensions/770924776838397952', 
    #   'display_name': 'Code Interpreter', 
    #   'description': 'N/A'}]
    ```

    Creating an extension example as per:
    https://cloud.google.com/vertex-ai/generative-ai/docs/extensions/create-extension

    ```python
    ## validates before upload
    vex.upload_openapi_file("your-extension-name.yaml")
    vex.openapi_file_gcs
    # 'gs://your-extensions-bucket/your-extension-name.yaml'

    ## load in examples to be used by creation later
    vex.load_tool_use_examples('your-examples.yaml')

    vex.create_extension(
        "My New Extension", 
        description="Querying the VAC above my database", 
        service_account='sa-serviceaccount@my-project.iam.gserviceaccount.com')
    ```

    Call the extension
    ```python
    operation_params = {"input": {"question":"This needs to be in same schema as your openapi spec"}
    vex.execute_extension("an_operation_id_from_your_openai_spec", 
                          operation_params = operation_params)
    ```
    """
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
        self.openapi_file_gcs = None
        self.tool_use_examples = None
        self.manifest = {}
        self.created_extensions = []

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
    
    def validate_openapi(self, filename):
        try:
            from openapi_spec_validator import validate
            from openapi_spec_validator.readers import read_from_filename
        except ImportError:
            raise ImportError("Must have openapi-spec-validator installed - install via `pip install sunholo[tools]`")
        
        spec_dict, spec_url = read_from_filename(filename)
        validate(spec_dict)
    
    def upload_to_gcs(self, filename):
        if not os.getenv('EXTENSIONS_BUCKET'):
            raise ValueError('Please specify env var EXTENSIONS_BUCKET for location to upload openapi spec')
        
        from ..gcs.add_file import add_file_to_gcs
        file_base = os.path.basename(filename)

        self_uri = add_file_to_gcs(file_base, bucket_filepath=file_base)

        return self_uri
    
    def upload_openapi_file(self, filename: str):
        self.validate_openapi(filename)

        self.openapi_file_gcs = self.upload_to_gcs(filename)
    
    def load_tool_use_examples(self, filename: str):
        import yaml

        with open(filename, 'r') as file:
            self.tool_use_examples = yaml.safe_load(file)

        # google.cloud.aiplatform_v1beta1.types.ToolUseExample
        return self.tool_use_examples
    

    def update_tool_use_examples_via_patch(self):
        import requests
        import json
        from google.auth import default
        from google.auth.transport.requests import Request

        extension = self.created_extension
        if extension is None:
            raise ValueError("Need to create the extension first")

        # Get the access token using Google authentication
        credentials, project_id = default()
        credentials.refresh(Request())
        access_token = credentials.token

        ENDPOINT=f"{self.location}-aiplatform.googleapis.com"
        URL=f"https://{ENDPOINT}/v1beta1"

        extension_id = self.created_extension.resource_name

        # Define the URL and extension ID
        url = f"{URL}/{extension_id}"
        log.info(f"PATCH {url}")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Define the payload
        payload = {
            "toolUseExamples": self.tool_use_examples['tool_use_examples']
        }

        # Make the PATCH request
        response = requests.patch(
            url,
            headers=headers,
            params={"update_mask": "toolUseExamples"},
            data=json.dumps(payload)
        )

        # Check the response
        if response.status_code == 200:
            log.info("Tool use examples updated successfully.")
        else:
            log.info(f"Failed to update tool use examples. Status code: {response.status_code}, Response: {response.text}")
        

    def create_extension_manifest(self,
                                  display_name,
                                  description,
                                  open_api_gcs_uri: str, 
                                  service_account: str):

        self.manifest = {
                "name": display_name,
                "description": description,
                "apiSpec": {
                    "openApiGcsUri": open_api_gcs_uri,
                },
                "authConfig": {
                    "authType": "OAUTH",
                    "oauthConfig": {"service_account": service_account}
                }
        }

        return self.manifest

    def create_extension(self,
                         display_name: str,
                         description: str,
                         open_api_file: str = None,
                         tool_example_file: str = None,
                         runtime_config: dict = None,
                         service_account: str = None):
        
        project_id = get_gcp_project()
        extension_name = f"projects/{project_id}/locations/us-central1/extensions/{validate_extension_id(display_name)}"

        if open_api_file:
            self.upload_openapi_file(open_api_file)

        manifest = self.create_extension_manifest(
            display_name,
            description,
            open_api_gcs_uri = self.openapi_file_gcs, 
            service_account = service_account, 
        )

        if tool_example_file:
            self.load_tool_use_examples(tool_example_file)

        extension = extensions.Extension.create(
            extension_name=extension_name,
            display_name=display_name,
            description=description,
            runtime_config=runtime_config or None, # sets things like what bucket will be used
            manifest=manifest,
            #tool_use_examples=self.tool_use_examples
        )
        log.info(f"Created Vertex Extension: {extension_name}")
        
        self.created_extension = extension

        if tool_example_file:
            self.update_tool_use_examples_via_patch()

        return extension.resource_name

    def execute_extension(self, operation_id: str, operation_params: dict, extension_id: str=None):
        init_vertex(location=self.location)

        if not extension_id:
            extension_name = self.created_extension.resource_name
            if extension_name is None:
                raise ValueError("Must specify extension_id or init one with class")
        else:  
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