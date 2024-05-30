import os
from fnmatch import fnmatch

def has_text_extension(file_path):
    """
    Check if a file has a common text or code file extension.

    Args:
        file_path (str): The path to the file.

    Returns:
        bool: True if the file has a text extension, False otherwise.
    
    Examples:
        >>> has_text_extension("example.txt")
        True
        >>> has_text_extension("example.pdf")
        False
    """
    # Define a set of common text and code file extensions
    text_extensions = {
        '.txt', '.md', '.py', '.json', '.xml', '.csv', '.html', '.htm',
        '.css', '.js', '.java', '.c', '.cpp', '.h', '.hpp', '.r', '.sh',
        '.bat', '.ini', '.yaml', '.yml', '.toml', '.pl', '.rb', '.go', 
        '.ts', '.tsx', '.rs', '.swift', '.kt', '.kts', '.scala', '.sql'
    }
    # Get the file extension and check if it's in the set
    _, ext = os.path.splitext(file_path)
    return ext.lower() in text_extensions

def load_gitignore_patterns(gitignore_path):
    """
    Load .gitignore file and compile ignore patterns.

    Args:
        gitignore_path (str): The path to the .gitignore file.

    Returns:
        list: A list of patterns to ignore.
    
    Examples:
        >>> patterns = load_gitignore_patterns("path/to/source/folder/.gitignore")
    """
    with open(gitignore_path, 'r') as f:
        patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    patterns.extend(["*.git/*", "*.terraform/*"])
    return patterns

def should_ignore(file_path, patterns):
    """
    Check if a file path matches any of the ignore patterns.

    Args:
        file_path (str): The path to the file.
        patterns (list): A list of patterns to ignore.

    Returns:
        bool: True if the file should be ignored, False otherwise.
    
    Examples:
        >>> should_ignore("path/to/file.txt", ["*.txt", "node_modules/"])
        True
    """
    rel_path = os.path.relpath(file_path)

    for pattern in patterns:
        if fnmatch(rel_path, pattern) or fnmatch(os.path.basename(rel_path), pattern):
            return True

    return False


def build_file_tree(source_folder, patterns):
    """
    Build a hierarchical file tree structure of a directory, ignoring files and directories in .gitignore.

    Args:
        source_folder (str): The root directory to build the file tree from.
        patterns (list): A list of patterns to ignore.

    Returns:
        list: A list of strings representing the file tree structure.
    
    Examples:
        >>> build_file_tree("path/to/source/folder", patterns)
        ['source_folder/', '    file1.txt', '    subfolder/', '        file2.py']
    """
    file_tree = []
    for root, dirs, files in os.walk(source_folder):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d), patterns)]
        # Filter out ignored files
        files = [f for f in files if not should_ignore(os.path.join(root, f), patterns)]
        
        level = root.replace(source_folder, '').count(os.sep)
        indent = ' ' * 4 * (level)
        file_tree.append(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            file_tree.append(f"{sub_indent}{f}")
    return file_tree

def merge_text_files(source_folder, output_file, patterns):
    """
    Merge the contents of all readable text files in a directory into one file.
    Also append the file tree structure at the end of the output file.

    Args:
        source_folder (str): The directory containing the text files to merge.
        output_file (str): The path to the output file where contents will be written.
        patterns (list): A list of patterns to ignore.

    Examples:
        >>> merge_text_files("path/to/source/folder", "path/to/output/bigfile.txt", patterns)
    """
    file_tree = build_file_tree(source_folder, patterns)
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(source_folder):
            print(f"- merging {root}...")
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d), patterns)]
            # Filter out ignored files
            files = [f for f in files if not should_ignore(os.path.join(root, f), patterns)]
            
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if file_path == output_file:
                    continue
                if has_text_extension(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(f"--- Start of {file_path} ---\n")
                            outfile.write(infile.read())
                            outfile.write(f"\n--- End of {file_path} ---\n\n")
                    except (IOError, UnicodeDecodeError):
                        print(f"Skipping file (cannot read as text): {file_path}")
        outfile.write("\n--- File Tree ---\n")
        outfile.write("\n".join(file_tree))
    
    return file_tree

# Example usage
if __name__ == "__main__":
    source_folder = 'sunholo'
    output_file = 'bigfile.txt'
    gitignore_path = os.path.join(source_folder, '.gitignore')
    
    if os.path.exists(gitignore_path):
        patterns = load_gitignore_patterns(gitignore_path)
    else:
        patterns = []  # Empty list if no .gitignore

    merge_text_files(source_folder, output_file, patterns)
