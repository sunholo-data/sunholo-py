try:
    import hcl2
except ImportError:
    hcl2 = None

import json
import subprocess
import os
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
            The directory where Terraform commands will be executed (default is current directory).

        Example:
        -------
        editor = TerraformVarsEditor('example.tfvars', '/path/to/terraform/config')
        """
        if hcl2 is None:
            raise ImportError('hcl2 is required for parsing terraform files, install via `pip install sunholo[iac]`')
        
        self.tfvars_file = tfvars_file
        self.terraform_dir = terraform_dir
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
        backup_file = f"{self.tfvars_file}.bak"
        os.rename(self.tfvars_file, backup_file)
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
        -------
        editor.update_or_add_instance('cloud_run', 'new_service', {'cpu': '1', 'memory': '2Gi'})
        """
        if main_key not in self.tfvars_data:
            self.tfvars_data[main_key] = {}

        self.tfvars_data[main_key][instance_name] = instance_data

    def validate_terraform(self) -> bool:
        """
        Runs `terraform validate` in the specified directory.

        Returns:
        -------
        bool
            True if validation passes, False otherwise.

        Example:
        -------
        if self.validate_terraform():
            print("Validation passed.")
        """
        result = subprocess.run(['terraform', 'validate'], cwd=self.terraform_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            log.info("Terraform validation passed.")
            return True
        else:
            log.error("Terraform validation failed.")
            print(result.stdout)
            print(result.stderr)
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
            self._restore_tfvars(backup_file)
            log.error(f"Changes aborted, original {self.tfvars_file} restored.")
        else:
            log.info(f"Terraform validation passed, changes saved to {self.tfvars_file}.")
            os.remove(backup_file)  # Remove the backup if validation passes

def tfvars_command(args):
    """
    Executes the tfvars command based on parsed arguments.

    Args:
        args: The parsed command-line arguments.
    """

    if console is None:
        raise ImportError("Need cli tools to use `sunholo tfvars` - install via `pip install sunholo[cli]`")
    
    # Parse the JSON string to a dictionary
    try:
        instance_data: Dict[str, Any] = json.loads(args.json_data)
    except json.JSONDecodeError as e:
        console.print(f"[bold red]Error parsing JSON data: {e}[/bold red]")
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
    add_parser.add_argument('json_data', help='JSON string representing the instance data')
    add_parser.add_argument('--terraform-dir', default='.', help='The directory where Terraform is initialized')

    tfvars_parser.set_defaults(func=tfvars_command)

    # If no subcommand is provided, print the help message
    tfvars_parser.set_defaults(func=lambda args: tfvars_parser.print_help() if args.action is None else tfvars_command)

