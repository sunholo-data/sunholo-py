try:
    import hcl2
except ImportError:
    hcl2 = None

import json
import subprocess
from datetime import datetime
import shutil
import os
import io
from typing import Dict, Any
from ..custom_logging import log

try:
    from ..cli.sun_rich import console
except ImportError:
    console = None

class TerraformVarsEditor:
    """
    A class to manage and safely edit Terraform .tfvars files.

    This class allows you to update specific keys in a .tfvars file with new data
    and ensures that the changes only take effect if Terraform validation passes.

    Attributes:
    ----------
    tfvars_file : str
        The path to the .tfvars file to be edited.
    terraform_dir : str
        The directory where Terraform commands will be executed (default is current directory).
    tfvars_data : dict
        The content of the .tfvars file loaded into a dictionary.
    
    Methods:
    -------
    _load_tfvars() -> Dict[str, Any]
        Loads the .tfvars file into a dictionary.
    _save_tfvars() -> None
        Saves the current state of the dictionary back to the .tfvars file.
    _backup_tfvars() -> str
        Creates a backup of the current .tfvars file.
    _restore_tfvars(backup_file: str) -> None
        Restores the .tfvars file from the backup.
    update_or_add_instance(main_key: str, instance_name: str, instance_data: Dict[str, Any]) -> None
        Adds or updates an instance under a specified top-level key in the .tfvars file.
    validate_terraform() -> bool
        Runs `terraform validate` in the specified directory.
    update_from_json(json_file: str, main_key: str) -> None
        Updates the .tfvars file based on the content of a JSON file and validates the changes.
    """

    def __init__(self, tfvars_file: str, terraform_dir: str = '.') -> None:
        """
        Initializes the TerraformVarsEditor with the given .tfvars file and Terraform directory.

        Parameters:
        ----------
        tfvars_file : str
            The path to the .tfvars file to be edited.
        terraform_dir : str
            The directory where Terraform commands will be executed (default is current directory). Will use MULTIVAC_TERRAFORM_DIR env var if present.

        Example:
        -------
        editor = TerraformVarsEditor('example.tfvars', '/path/to/terraform/config')
        """
        if hcl2 is None:
            raise ImportError('hcl2 is required for parsing terraform files, install via `pip install sunholo[iac]`')

        # Check for the MULTIVAC_TERRAFORM_DIR environment variable
        if terraform_dir == '.' and 'MULTIVAC_TERRAFORM_DIR' in os.environ:
            terraform_dir = os.environ['MULTIVAC_TERRAFORM_DIR']
        
        log.info(f'MULTIVAC_TERRAFORM_DIR environment variable is set to {terraform_dir}')
        
        self.tfvars_file = tfvars_file
        self.terraform_dir = terraform_dir

        # Ensure the tfvars file exists, if not, create it
        if not os.path.exists(self.tfvars_file):
            log.info(f"{self.tfvars_file} does not exist. Creating a new file.")
            with open(self.tfvars_file, 'w') as file:
                file.write("")  # Create an empty tfvars file
                
        self.tfvars_data = self._load_tfvars()

    def _load_tfvars(self) -> Dict[str, Any]:
        """
        Loads the .tfvars file into a dictionary.

        Returns:
        -------
        dict
            The content of the .tfvars file.

        Example:
        -------
        data = self._load_tfvars()
        """
        with open(self.tfvars_file, 'r') as file:
            return hcl2.load(file)

    def _save_tfvars(self) -> None:
        """
        Saves the current state of the dictionary back to the .tfvars file.

        Example:
        -------
        self._save_tfvars()
        """
        with open(self.tfvars_file, 'w') as file:
            for key, value in self.tfvars_data.items():
                file.write(f'{key} = {json.dumps(value, indent=2)}\n')

    def _backup_tfvars(self) -> str:
        """
        Creates a backup of the current .tfvars file.

        Returns:
        -------
        str
            The path to the backup file.

        Example:
        -------
        backup_file = self._backup_tfvars()
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_file = f"{self.tfvars_file}.{timestamp}.bak"
        shutil.copy2(self.tfvars_file, backup_file)
        return backup_file

    def _restore_tfvars(self, backup_file: str) -> None:
        """
        Restores the .tfvars file from the backup.

        Parameters:
        ----------
        backup_file : str
            The path to the backup file to restore from.

        Example:
        -------
        self._restore_tfvars('example.tfvars.bak')
        """
        os.rename(backup_file, self.tfvars_file)

    def update_or_add_instance(self, main_key: str, instance_name: str, instance_data: Dict[str, Any]) -> None:
        """
        Adds or updates an instance under a specified top-level key in the .tfvars file.

        Parameters:
        ----------
        main_key : str
            The top-level key in the .tfvars file (e.g., "cloud_run").
        instance_name : str
            The name of the instance to add or update.
        instance_data : dict
            The dictionary containing the instance data.

        Example:
        
        ```python
        editor.update_or_add_instance('cloud_run', 'new_service', (your dict))
        ```
        """
        if main_key not in self.tfvars_data:
            self.tfvars_data[main_key] = {}

        self.tfvars_data[main_key][instance_name] = instance_data

    def validate_terraform(self) -> bool:
        """
        Runs `terraform init` followed by `terraform validate` in the specified directory.

        Returns:
        -------
        bool
            True if validation passes, False otherwise.

        Example:
        -------
        ```python
        if self.validate_terraform():
            print("Validation passed.")
        ```
        """
        # Step 1: Run `terraform init` to ensure the directory is initialized
        init_process = subprocess.run(['terraform', 'init'], cwd=self.terraform_dir, capture_output=True, text=True)
        
        if init_process.returncode != 0:
            log.error("Terraform initialization failed.")
            print(init_process.stdout)
            print(init_process.stderr)
            return False
        
        log.info("Terraform initialized successfully.")

        # Step 2: Run `terraform validate`
        validate_process = subprocess.run(['terraform', 'validate'], cwd=self.terraform_dir, capture_output=True, text=True)
        
        if validate_process.returncode == 0:
            log.info("Terraform validation passed.")
            return True
        else:
            log.error("Terraform validation failed.")
            print(validate_process.stdout)
            print(validate_process.stderr)
            return False

    def update_from_json(self, json_file: str, main_key: str) -> None:
        """
        Updates the .tfvars file based on the content of a JSON file and validates the changes.

        Parameters:
        ----------
        json_file : str
            The path to the JSON file with the new instance data.
        main_key : str
            The top-level key in the .tfvars file (e.g., "cloud_run").

        Example:
        -------
        editor.update_from_json('update.json', 'cloud_run')
        """
        with open(json_file, 'r') as file:
            data = json.load(file)

        # Update the tfvars data in memory
        for instance_name, instance_data in data.get(main_key, {}).items():
            self.update_or_add_instance(main_key, instance_name, instance_data)

        # Backup the original .tfvars file
        backup_file = self._backup_tfvars()

        # Temporarily save the updated data to the original file location
        self._save_tfvars()

        # Attempt to validate the changes with Terraform
        if not self.validate_terraform():
            # If validation fails, restore the original file from the backup
            failed_file = f"{self.tfvars_file}.failed"
            shutil.copy2(self.tfvars_file, failed_file)
            self._restore_tfvars(backup_file)
            print(f"Changes aborted, original {self.tfvars_file} restored. Failed file: {failed_file}")
        else:
            log.info(f"Terraform validation passed, changes saved to {self.tfvars_file}.")
            os.remove(backup_file)  # Remove the backup if validation passes

    def update_from_dict(self, data: Dict[str, Any], main_key: str) -> None:
        """
        Updates the .tfvars file based on the content of a Python dictionary and validates the changes.

        Parameters:
        ----------
        data : dict
            The dictionary with the new instance data.
        main_key : str
            The top-level key under which the instance is added (e.g., "cloud_run").

        Example:
        -------
        editor.update_from_dict(data, 'cloud_run')
        """
        # Create an in-memory file-like object from the dictionary by converting it to JSON
        json_data = json.dumps({main_key: data})
        json_file = io.StringIO(json_data)

        # Load the JSON data from the StringIO object
        parsed_data = json.load(json_file)

        # Update the tfvars data in memory
        for instance_name, instance_data in parsed_data.get(main_key, {}).items():
            self.update_or_add_instance(main_key, instance_name, instance_data)

        # Now that the data is updated in memory, proceed to validate and write it back to the file
        # Backup the original .tfvars file
        backup_file = self._backup_tfvars()

        # Temporarily save the updated data to the original file location
        self._save_tfvars()

        # Attempt to validate the changes with Terraform
        if not self.validate_terraform():
            # If validation fails, restore the original file from the backup
            failed_file = f"{self.tfvars_file}.failed"
            shutil.copy2(self.tfvars_file, failed_file)
            self._restore_tfvars(backup_file)

            print(f"Changes aborted, original {self.tfvars_file} restored. Failed file: {failed_file}")
        else:
            console.print(f"Terraform validation passed, changes saved to {self.tfvars_file}.")
            os.remove(backup_file)  # Remove the backup if validation passes

def tfvars_command(args):
    """
    Executes the tfvars command based on parsed arguments.

    Args:
        args: The parsed command-line arguments.
    """

    if console is None:
        raise ImportError("Need cli tools to use `sunholo tfvars` - install via `pip install sunholo[cli]`")
    
    # Load JSON data from the specified file
    try:
        with open(args.json_file, 'r') as f:
            instance_data = json.load(f)
    except FileNotFoundError:
        console.print(f"Error: The JSON file '{args.json_file}' was not found.")
        return
    except json.JSONDecodeError as e:
        console.print(f"Error parsing JSON data: {e}")
        return

    # Create an instance of TerraformVarsEditor
    editor = TerraformVarsEditor(args.tfvars_file, args.terraform_dir)

    # Add or update the instance
    editor.update_or_add_instance(args.main_key, args.instance_name, instance_data)

    # Validate the Terraform configuration
    if editor.validate_terraform():
        console.print(f"Successfully updated '{args.instance_name}' under '{args.main_key}' in '{args.tfvars_file}'.")
    else:
        console.print(f"[bold red]Failed to update '{args.instance_name}'. The changes have been rolled back.[/bold red]")

def setup_tfvarseditor_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'tfvars' command.

    Args:
        subparsers: The subparsers object from argparse.ArgumentParser().
    """
    # TFVars subparser setup
    tfvars_parser = subparsers.add_parser('tfvars', help='Manage Terraform .tfvars files')
    tfvars_subparsers = tfvars_parser.add_subparsers(dest='action', help='TFVars subcommands')

    # TFVars add command
    add_parser = tfvars_subparsers.add_parser('add', help='Add or update an instance in a .tfvars file')
    add_parser.add_argument('tfvars_file', help='Path to the .tfvars file')
    add_parser.add_argument('main_key', help='The main key under which the instance is added (e.g., "cloud_run")')
    add_parser.add_argument('instance_name', help='The name of the instance to add or update')
    add_parser.add_argument('--json-file', help='Path to a JSON file with the instance data', required=True)
    add_parser.add_argument('--terraform-dir', default='.', help='The directory where Terraform is initialized')

    tfvars_parser.set_defaults(func=tfvars_command)

    # If no subcommand is provided, print the help message
    tfvars_parser.set_defaults(func=lambda args: tfvars_parser.print_help() if args.action is None else tfvars_command)

