import os
from pprint import pprint

from ..utils.big_context import load_gitignore_patterns, merge_text_files

def setup_merge_text_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'merge-text' command.

    Args:
        subparsers: The subparsers object from argparse.ArgumentParser().
    """
    merge_text_parser = subparsers.add_parser('merge-text', help='Merge text files from a source folder into a single output file.')
    merge_text_parser.add_argument('source_folder', help='Folder containing the text files.')
    merge_text_parser.add_argument('output_file', help='Output file to write the merged text.')
    merge_text_parser.add_argument('--gitignore', help='Path to .gitignore file to exclude patterns.', default=None)
    merge_text_parser.add_argument('--output_tree', action='store_true', help='Set to output the file tree in the console after merging', default=None)
        
    merge_text_parser.set_defaults(func=merge_text_files_command)

def merge_text_files_command(args):
    """
    Command to merge text files based on the provided arguments.
    
    Args:
        args: Command-line arguments.
    """
    gitignore_path = os.path.join(args.source_folder, '.gitignore') if not args.gitignore else args.gitignore

    if os.path.exists(gitignore_path):
        patterns = load_gitignore_patterns(gitignore_path)
        print(f"Ignoring patterns from {gitignore_path}")
    else:
        patterns = []  # Empty list if no .gitignore

    print(f"Merging text files within {args.source_folder} to {args.output_file}")
    file_tree = merge_text_files(args.source_folder, args.output_file, patterns)
    print(f"OK: Merged files available in {args.output_file}")
    if args.output_tree:
        print(f"==File Tree for {args.source_folder}")
        pprint(file_tree)
