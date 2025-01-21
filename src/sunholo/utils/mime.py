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

