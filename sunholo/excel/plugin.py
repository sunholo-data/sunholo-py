import os
import sys
import subprocess
import shutil
from ..custom_logging import log
from ..invoke import direct_vac

def setup_excel_plugin(args):
    """
    Sets up the Excel plugin by copying the VBA file and creating the xlwings.conf file 
    with the correct Python interpreter path.
    """
    from rich.panel import Panel
    from ..cli.sun_rich import console

    # Define the source directory (where the sunholo.excel package is located)
    library_folder = os.path.dirname(__file__)
    
    # Define the destination directory (current working directory)
    destination_folder = os.getcwd()
    
    # Define the paths
    vba_file_template = "call_vac.vba.template"  # A template file with a placeholder for the path
    vba_file_output = "call_vac.vba"
    source_vba_file = os.path.join(library_folder, vba_file_template)
    destination_vba_file = os.path.join(destination_folder, vba_file_output)
    
    # Ensure the .venv directory exists
    if not os.path.exists(os.path.join(destination_folder, ".venv")):
        console.print(f"ERROR: Virtual environment not found in {destination_folder}. "
                      "Please ensure you are working in correct folder. " 
                      " This command needs to be run from location where venv is created via `python -m venv .venv`"
                      " and has installed this library via `pip install sunholo[excel]`")
        return None

    # Create the xlwings.conf file with the correct Python interpreter path
    conf_file_path = os.path.join(destination_folder, "xlwings.conf")
    python_executable = sys.executable

    # Ensure the .venv directory exists
    if not os.path.exists(os.path.dirname(python_executable)):
        console.print(f"[bold red]ERROR: Python environment not found at {python_executable}. Please ensure it is created.[/bold red]")
        return None

    # Check if xlwings is installed
    try:
        subprocess.run([python_executable, "-c", "import xlwings"], check=True, capture_output=True)
        console.print("xlwings is installed in the Python environment.")
    except subprocess.CalledProcessError:
        console.print("[bold red]WARNING: xlwings is not installed in the Python environment. Please install it using 'pip install sunholo\[excel]'[/bold red]")

    
    # Write the xlwings.conf file
    try:
        with open(conf_file_path, "w") as conf_file:
            conf_file.write("[Interpreter]\n")
            conf_file.write(f"PYTHONPATH={python_executable}\n")
        console.print(f"Created {conf_file_path} with PYTHONPATH set to {python_executable}")
    except IOError as e:
        console.print(f"[bold red]ERROR:[/bold red] Failed to create xlwings.conf: {e}")
        return None

    # Copy the VBA template file to the destination as the VBA file
    try:
        shutil.copy2(source_vba_file, destination_vba_file)
        console.print(f"Created {destination_vba_file}")
    except IOError as e:
        console.print(f"[bold red]ERROR:[/bold red] Failed to copy VBA file: {e}")
        return None
    
    console.print(
        Panel(("1. Open your Excel workbook.\n"
                "2. Press Alt + F11 to open the VBA editor.\n"
                "3. Insert a new module (Insert -> Module).\n"
                f"4. Add the VBA code from {destination_vba_file} into the module.\n"
                "5. Use =MULTIVAC() within your Excel cells"), 
        title="Next Steps")
        )
    

def excel_plugin(input_data, vac_name):
    log.info(f"Calling multivac plugin for {vac_name} with {input_data}")
    response = direct_vac(input_data, vac_name=vac_name)
    log.info(f"Plugin got {response}")
    return response['answer']

def setup_excel_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'excel' command.

    Example command:
    ```bash
    sunholo excel-init
    ```
    """
    deploy_parser = subparsers.add_parser('excel-init', help='Create Excel integrations with Sunholo VACs')
    deploy_parser.set_defaults(func=setup_excel_plugin)