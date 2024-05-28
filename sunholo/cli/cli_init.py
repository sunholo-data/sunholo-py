import os
import shutil
from ..utils.config import get_module_filepath

def init_project(args):
    """
    Initializes a new sunholo project with a basic configuration file and directory structure.

**Explanation:**

1. **Import Necessary Modules:**
   - `os` for file system operations.
   - `shutil` for copying files and directories.
   - `log` from `sunholo.logging` for logging messages.
   - `get_module_filepath` from `sunholo.utils.config` to get the absolute path of template files.

2. **`init_project` Function:**
   - Takes an `args` object from argparse, containing the `project_name`.
   - Creates the project directory using `os.makedirs`.
   - Copies template files from the `templates/project` directory to the new project directory using `shutil.copy` and `shutil.copytree`.
   - Logs informative messages about the initialization process.

3. **`setup_init_subparser` Function:**
   - Sets up the `init` subcommand for the `sunholo` CLI.
   - Adds an argument `project_name` to specify the name of the new project.
   - Sets the `func` attribute to `init_project`, so the parser knows which function to call when the `init` command is used.

**Template Files (`templates/project`):**

You'll need to create a `templates/project` directory within your `sunholo` package and place the following template files in it:

* **`config/llm_config.yaml`:** A basic configuration file with placeholders for LLM settings, vector stores, etc.
* **`config/cloud_run_urls.json`:** A template for Cloud Run URLs.
* **`app.py`:** A basic Flask app that can be customized for the project.
* **`.gitignore`:** A gitignore file to exclude unnecessary files from version control.
* **`README.md`:** A README file with instructions for setting up and running the project.

**Usage:**

After adding this code to your `cli.py` and creating the template files, users can initialize a new project using the following command:

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
    init_parser = subparsers.add_parser('init', help='Initializes a new sunholo project.')
    init_parser.add_argument('project_name', help='The name of the new project.')
    init_parser.set_defaults(func=init_project)
