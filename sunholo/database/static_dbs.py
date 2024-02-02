import os
from ..logging import log_folder_location

def get_db_directory(db_dir='db'):
    current_script_directory = os.path.dirname(os.path.abspath(__file__))
    # Get the parent directory of the current script directory
    parent_directory = os.path.abspath(os.path.join(current_script_directory, os.pardir))
    db_directory = os.path.join(parent_directory, db_dir)
    log_folder_location(db_directory)

    return db_directory