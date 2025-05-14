import os
import json

from ..custom_logging import log
from ..utils.mime import get_mime_type_gemini
from .metadata import check_gcs_file_size
from .download_url import get_bytes_from_gcs

def download_gcs_source_to_string(source:str, max_size_bytes: int = 1024*1024) -> str:
    """
    Download a file from Google Cloud Storage and convert it to a string.
    
    Args:
        source: str The Google Cloud Storage URI of the file to download (e.g., 'gs://bucket_name/file_name').
        max_size_bytes: int Maximum file size to download, defaults to 1MB (1024*1024 bytes)
        
    Returns:
        str: The contents of the file as a string, or an empty string if the file could not be downloaded.
    """

    mime_type = get_mime_type_gemini(source)
    if mime_type == "":
        log.warning(f"Can not download to string file source {source}")
        return ""
    """
        mime_types = {

        # Images
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'webp': 'image/webp',

        # Document formats
        'pdf': 'application/pdf',
        
        # Programming languages
        'js': 'text/javascript',
        'py': 'text/x-python',
        
        # Web formats
        'html': 'text/html',
        'htm': 'text/html',
        'css': 'text/css',
        
        # Text formats
        'txt': 'text/plain',
        'md': 'text/md',
        'csv': 'text/csv',
        'xml': 'text/xml',
        'rtf': 'text/rtf',
        
        # Special case: JSON files are treated as plain text
        'json': 'text/plain'
    }
    """
    if mime_type.startswith("image/") or mime_type == "application/pdf":
        log.warning(f"Can not download to string file source {source} of type {mime_type}")
        return ""

    try:
        log.info(f"Extracting text for {source}")
        # Check file size before downloading
        file_size = check_gcs_file_size(source)
        if file_size == -1:
            log.warning(f"Could not determine file size for {source}")
            return ""
        elif file_size > max_size_bytes:
            log.warning(f"File size {file_size} bytes exceeds maximum size limit of {max_size_bytes} bytes for {source}")
            return ""
        
        bytes = get_bytes_from_gcs(source)
        string = bytes.decode('utf-8', errors='replace')
        log.info(f"Extracted {len(string)} characters from {source}: {string[:100]}")

    except Exception as err:
        log.error(f"Could not extract string text for {source}: {str(err)}")

        return ""

    if not string:
        raise ValueError(f"No string text for {source}")

    file_ext = os.path.splitext(source)[1].lower().lstrip('.')
    if file_ext == "json":
        try:
            extracted_data = json.loads(string)
            log.debug("Turning json text into markdown format so as not to confuse structured output", log_struct=extracted_data)
            string = json_data_to_markdown(extracted_data)
        except json.JSONDecodeError:
            log.warning(f"Could not get valid json from .json file: {source}")
    
    return string

def json_data_to_markdown(data, indent_level: int = 0) -> str:
    """
    Recursively converts a Python object (from parsed JSON) into a Markdown string.
    """
    indent = "  " * indent_level  # Use 2 spaces for indentation
    markdown_parts = []

    if isinstance(data, dict):
        if not data:
            return f"{indent}(empty object)"
        for key, value in data.items():
            # Process the value recursively
            value_md = json_data_to_markdown(value, indent_level + 1)
            # Determine if the rendered value is complex (multi-line or was list/dict)
            is_complex_render = "\n" in value_md.strip() or (isinstance(value, (dict, list)) and value)

            if is_complex_render:
                markdown_parts.append(f"{indent}**{key}**:")
                markdown_parts.append(value_md)
            else:
                # Simple value rendering, strip its own indent before adding key
                markdown_parts.append(f"{indent}**{key}**: {value_md.strip()}")
        return "\n".join(markdown_parts)

    elif isinstance(data, list):
        if not data:
            return f"{indent}(empty list)"
        for item in data:
            # Process item recursively
            item_md = json_data_to_markdown(item, indent_level + 1)
            # Remove leading indent from the recursive call before processing lines
            lines = item_md.lstrip(' ').split('\n')
            # Add bullet point to the first line
            first_line = f"{indent}- {lines[0]}"
            # Ensure subsequent lines are indented correctly relative to the bullet
            rest_lines = [f"{indent}  {line}" for line in lines[1:]]
            markdown_parts.append(first_line)
            markdown_parts.extend(rest_lines)
        return "\n".join(markdown_parts)

    elif isinstance(data, str):
        # Handle multi-line strings: indent subsequent lines
        lines = data.split('\n')
        if len(lines) <= 1:
            return f"{indent}{data}" # Single line string
        else:
            indented_lines = [f"{indent}{lines[0]}"] + [f"{indent}  {line}" for line in lines[1:]]
            return "\n".join(indented_lines)

    elif data is None:
        return f"{indent}*null*" # Represent None distinctly
    elif isinstance(data, bool):
        return f"{indent}{str(data).lower()}" # true / false
    else:  # Numbers (int, float)
        return f"{indent}{str(data)}"