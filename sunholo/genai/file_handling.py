from ..custom_logging import log
from ..gcs import get_bytes_from_gcs

import mimetypes
import asyncio
import tempfile
import re
import traceback
try:
    import google.generativeai as genai
    from google.generativeai.types import file_types
except ImportError:
    genai = None
    file_types = None
    
DOCUMENT_MIMES = [
    'application/pdf',
    'application/x-javascript',
    'text/javascript',
    'application/x-python',
    'text/x-python',
    'text/plain',
    'text/html',
    'text/css',
    'text/md',
    'text/csv',
    'text/xml',
    'text/rtf'
    ]

IMAGE_MIMES = [
    'image/png',
    'image/jpeg',
    'image/webp',
    'image/heic',
    'image/heif',
]

VIDEO_MIMES = [
    'video/mp4',
    'video/mpeg',
    'video/mov',
    'video/avi',
    'video/x-flv',
    'video/mpg',
    'video/webm',
    'video/wmv',
    'video/3gpp'
]

AUDIO_MIMES = [
    'audio/wav',
    'audio/mp3',
    'audio/aiff',
    'audio/aac',
    'audio/ogg',
    'audio/flac',    
]

ALLOWED_MIME_TYPES = set(AUDIO_MIMES + VIDEO_MIMES + IMAGE_MIMES + DOCUMENT_MIMES)

# 'documents': 
# [
#   {'storagePath': 'users/UQcKi4u7s...dsd.png', 
#    'url': 'https://firebasestorage.googleapis.com/v0/b/multi...', 
#    'contentType': 'image/png', 
#    'type': 'image', 
#    'name': 'multivac-data-architecture.png'}, 
#   {'storagePath': 'users/UQc...3dc59e1.jpg', 
#   'type': 'image', 
#   'name': 'holosun-circle.jpg', 
#   'url': 'https://firebasestorage.googleapis.com/v0/b/multiv...', 
#   'contentType': 'image/jpeg'}
# ]
async def construct_file_content(gs_list, bucket:str):
    """
    Args:
    - gs_list: a list of dicts representing files in a bucket
       - contentType: The content type of the file on GCS
       - storagePath: The path in the bucket
    - bucket: The bucket the files are in

    """
    
    file_list = []
    for element in gs_list:

        the_mime_type = element.get('contentType')
        if the_mime_type is None:
            continue
        if element.get('storagePath') is None:
            continue
        if the_mime_type in ALLOWED_MIME_TYPES:
            file_list.append(element)
    
    if not file_list:
        return {"role": "user", "parts": [{"text": "No eligible contentTypes were found"}]}

    content = []
    
    # Loop through the valid files and process them
    tasks = []
    for file_info in file_list:
        img_url = f"gs://{bucket}/{file_info['storagePath']}"
        mime_type = file_info['contentType']
        # Append the async download task to the task list
        tasks.append(download_gcs_upload_genai(img_url, mime_type))

    # Run all tasks in parallel
    content = await asyncio.gather(*tasks)

    return content

# Helper function to handle each file download with error handling
async def download_file_with_error_handling(img_url, mime_type):
    try:
        return await download_gcs_upload_genai(img_url, mime_type)
    except Exception as err:
        msg= f"Error processing file from {img_url}: {str(err)}"
        log.error(msg)
        return {"role": "user", "parts": [{"text": msg}]}

async def download_gcs_upload_genai(img_url, mime_type, retries=3, delay=2):
    import aiofiles
    """
    Downloads and uploads a file with retries in case of failure.
    
    Args:
      - img_url: str The URL of the file to download.
      - mime_type: str The MIME type of the file.
      - retries: int Number of retry attempts before failing.
      - delay: int Initial delay between retries, exponentially increasing.
      
    Returns:
      - downloaded_content: The result of the file upload if successful.
    """
    for attempt in range(retries):
        try:
            log.info(f"Upload {attempt} for {img_url=}")
            # Download the file bytes asynchronously
            file_bytes = await asyncio.to_thread(get_bytes_from_gcs, img_url)
            if not file_bytes:
                msg = f"Failed to download file from {img_url}: got None"
                log.warning(msg)
                return {"role": "user", "parts": [{"text": msg}]}
            
            # Log the size of the file bytes
            file_size = len(file_bytes)
            log.info(f"Downloaded file size for {img_url}: {file_size} bytes")

            if file_size > 19434343:
                log.warning(f"File size for {img_url}: {file_size} is too big.")
                msg =  f"The file for {img_url} is too large ({file_size} bytes) to be used directly.  Use RAG instead."
                return {"role": "user", "parts": [{"text": msg}]}
            
            extension = mimetypes.guess_extension(mime_type)
            
            # Use aiofiles for asynchronous file operations
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
            downloaded_file = temp_file.name

            sanitized_file = re.sub(r'[^\w\-.]', '_', downloaded_file)

            log.info(f"Writing file {sanitized_file}")
            async with aiofiles.open(sanitized_file, 'wb') as f:
                await f.write(file_bytes)

            # Upload the file and get its content reference
            try:
                downloaded_content: file_types.File = await asyncio.to_thread(genai.upload_file, sanitized_file )
                return {"role": "user", "parts": [{"file_data": downloaded_content}]}
            except Exception as err:
                msg = f"Could not upload {sanitized_file} to genai.upload_file: {str(err)} {traceback.format_exc()}"
                log.error(msg)
                return {"role": "user", "parts": [{"text": msg}]}
        
        except Exception as err:
            log.error(f"Error processing file {img_url} on attempt {attempt + 1}/{retries}: {str(err)}")

            if attempt < retries - 1:
                log.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise err  # Raise the error after max retries

