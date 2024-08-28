import os
import shutil
from ..utils.config import get_module_filepath

def init_project(args):
    """
    Initializes a new sunholo project with a basic configuration file and directory structure.

**Template Files (`templates/project`):**

A `templates/project` directory is within the `sunholo` package with the following template files in it:

* **`config/llm_config.yaml`:** A basic configuration file with placeholders for LLM settings, vector stores, etc.
* **`config/cloud_run_urls.json`:** A template for Cloud Run URLs.
* **`app.py`:** A basic Flask app that can be customized for the project.
* **`.gitignore`:** A gitignore file to exclude unnecessary files from version control.
* **`README.md`:** A README file with instructions for setting up and running the project.

**Usage:**

Users can initialize a new project using the following command:

```bash
sunholo init my_genai_project
```

This will create a new directory named `my_genai_project` with the template files, allowing users to start building their GenAI application.
    """
    project_name = args.project_name
    current_dir = os.getcwd()  # This captures the current directory where the command is run
    project_dir = os.path.join(current_dir, project_name)

    print(f"Initializing project: {project_name} in directory: {project_dir}")

    # Create project directory
    if os.path.exists(project_dir):
        print(f"Directory {project_dir} already exists. Please choose a different project name.")
        return

    os.makedirs(project_dir)

    # Copy template files
    template_dir = get_module_filepath("templates/project")
    for filename in os.listdir(template_dir):
        src_path = os.path.join(template_dir, filename)
        dest_path = os.path.join(project_dir, filename)
        if os.path.isfile(src_path):
            shutil.copy(src_path, dest_path)
        elif os.path.isdir(src_path):
            shutil.copytree(src_path, dest_path)

    # Determine the location of the generated.tfvars file
    terraform_dir = args.terraform_dir or os.getenv('MULTIVAC_TERRAFORM_DIR')
    if terraform_dir is None:
        raise ValueError("Must specify a terraform_dir or use the MULTIVAC_TERRAFORM_DIR environment variable")
    
    tfvars_file = os.path.join(terraform_dir, 'generated.tfvars')

    # Get the service account, either from the CLI argument or default
    service_account = args.service_account or "sa-llmops"  # Default service account

    # Determine the relative path for the cloud build included directories
    def get_relative_application_path(full_path: str, base_dir: str) -> str:
        application_base_index = full_path.find("application/")
        if application_base_index != -1:
            return full_path[application_base_index:]
        return os.path.relpath(full_path, base_dir)

    # Paths to be included in the cloud build (based on the current working directory)
    # We want paths to start from 'application/system_services/{project_name}'
    relative_base = os.path.relpath(current_dir, os.path.join(current_dir, "..", ".."))
    included_path = os.path.join(relative_base, project_name, "**")
    cloud_build_path = os.path.join(relative_base, project_name, "cloudbuild.yaml")

    # Define the cloud_run configuration for 'discord-server' with the correct project_dir path
    cloud_run_config = {
        project_name: {
            "cpu": "1",
            "memory": "2Gi",
            "max_instance_count": 3,
            "timeout_seconds": 1500,
            "port": 8080,
            "service_account": service_account,
            "invokers": ["allUsers"],
            "cloud_build": {
                "included": [included_path],
                "path": cloud_build_path,
                "substitutions": {},
                "repo_name": "",
                "repo_owner": ""
            }
        }
    }


    # Initialize the TerraformVarsEditor and update the .tfvars file
    try:
        from ..terraform import TerraformVarsEditor
        editor = TerraformVarsEditor(tfvars_file, terraform_dir)
        editor.update_from_dict(cloud_run_config, 'cloud_run')
        print(f"{tfvars_file} file initialized and updated successfully.")
    except ImportError as e:
        print(f"Error initializing TerraformVarsEditor: {e}")

    print(f"Project {project_name} initialized successfully.")
    print(f"Navigate to {project_dir} and customize the configuration files in the 'config' directory.")

def setup_init_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'init' command.
    """
    init_parser = subparsers.add_parser('init', help='Initializes a new Multivac project.')
    init_parser.add_argument('project_name', help='The name of the new project.')
    init_parser.add_argument('--terraform-dir', help='The directory where Terraform files will be generated.')
    init_parser.add_argument('--service-account', help='The service account to use for Cloud Run. Defaults to "sa-llmops"')
    init_parser.set_defaults(func=init_project)
