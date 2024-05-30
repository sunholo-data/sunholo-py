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
    project_dir = os.path.join(os.getcwd(), project_name)

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

    print(f"Project {project_name} initialized successfully.")
    print(f"Navigate to {project_dir} and customize the configuration files in the 'config' directory.")

def setup_init_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'init' command.
    """
    init_parser = subparsers.add_parser('init', help='Initializes a new Multivac project.')
    init_parser.add_argument('project_name', help='The name of the new project.')
    init_parser.set_defaults(func=init_project)
