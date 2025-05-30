import os
from ..custom_logging import log

def guess_mime_type(file_path: str) -> str:
    """
    Guess the mime type based on the file extension.

    Args:
        file_path (str): The path or URL of the image file.

    Returns:
        str: The guessed image type (e.g., "jpeg", "png", "gif", etc.)
             or None if the extension is not recognized.
    """
    # Extract the file extension
    _, ext = os.path.splitext(file_path)
    
    # Normalize and remove the leading dot
    ext = ext.lower().strip('.')

    # Mapping of common file extensions to file types
    log.info(f"Guessing {file_path} is {ext}")
    extension_to_type = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
        "tif": "image/tiff",
        "webp": "image/webp",
        "ico": "image/vnd.microsoft.icon",
        "svg": "image/svg+xml",
        "pdf": "application/pdf",
        "txt": "text/plain",
        "md": "text/markdown",
        "html": "text/html",
        "css": "text/css",
        "js": "application/javascript",
        "json": "application/json",
        "xml": "application/xml",
        "csv": "text/csv",
        "py": "text/x-python",
        "java": "text/x-java-source",
        "c": "text/x-c",
        "cpp": "text/x-c++",
        "h": "text/x-c",
        "hpp": "text/x-c++",
        "sh": "application/x-sh",
        "bat": "application/x-msdos-program",
        "php": "application/x-httpd-php",
        "rb": "application/x-ruby",
        "pl": "application/x-perl",
        "swift": "application/x-swift",
        "r": "text/x-r",
        "go": "text/x-go",
        "sql": "application/sql",
        "yaml": "text/yaml",
        "yml": "text/yaml",
        "ts": "application/typescript",
        "tsx": "text/tsx",
        "jsx": "text/jsx",
    }
    mime=extension_to_type.get(ext, "")
    log.info(f"Guessing {file_path} with {ext=} is {mime=}")

    return mime


def get_mime_type_gemini(file_path:str) -> str:
    """
    Determine the MIME type based on file extension.
    Only returns valid Gemini formats, or None if they are not supported.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: The appropriate MIME type for the file
    """
    # Extract the file extension (lowercase)
    ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    
    # Define the mapping of extensions to MIME types
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
        'json': 'text/plain',
        
        # Audio
        'mp3': 'audio/mp3',
        'mpeg': 'audio/mpeg',
        'wav': 'audio/wav',
        
        # Video
        'mov': 'video/mov',
        'mp4': 'video/mp4',
        'mpg': 'video/mpeg',
        'avi': 'video/avi',
        'wmv': 'video/wmv',
        'flv': 'video/flv'
    }
    
    # Return the appropriate MIME type, defaulting to None if unknown
    return mime_types.get(ext, "")