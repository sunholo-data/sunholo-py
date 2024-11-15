from ..custom_logging import log
from ..gcs import get_bytes_from_gcs

from functools import partial
import mimetypes
import asyncio
import tempfile
import re
import os
import traceback
try:
    import google.generativeai as genai
except ImportError:
    genai = None

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
    'audio/mpeg', #added
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

def sanitize_file(filename):
    # Split the filename into name and extension
    name, extension = os.path.splitext(filename)
    
    # Sanitize the name by removing invalid characters and converting to lowercase
    sanitized_name = re.sub(r'[^a-z0-9-]', '', name.lower())
    sanitized_name = re.sub(r'^-+|-+$', '', sanitized_name)  # Remove leading or trailing dashes
    
    # Reattach the original extension
    return sanitized_name[:40]

async def construct_file_content(gs_list, bucket:str):
    """
    Args:
    - gs_list: a list of dicts representing files in a bucket
       - contentType: The content type of the file on GCS
       - storagePath: The path in the bucket
       - name: The name of the file
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
        else:
            log.warning(f'{the_mime_type} is not in allowed MIME types for {element.get("name")}')
    
    if not file_list:
        return {"role": "user", "parts": [{"text": "No eligible contentTypes were found"}]}

    content = []
    
    # Loop through the valid files and process them
    tasks = []
    for file_info in file_list:
        img_url = f"gs://{bucket}/{file_info['storagePath']}"
        display_url = file_info.get('url')
        mime_type = file_info['contentType']
        name = sanitize_file(file_info['name'])
        display_name = file_info['name']
        log.info(f"Processing {name=} {display_name=}")
        try:
            myfile = genai.get_file(name)
            content.append(
                {"role": "user", "parts": [
                    {"file_data": myfile}, 
                    {"text": f"You have been given the ability to work with file {display_name=} with {mime_type=} {display_url=}"}
                    ]
                })
            log.info(f"Found existing genai.get_file {name=}")
            
        except Exception as e:
            log.info(f"Not found checking genai.get_file: '{name}' {str(e)}")
            tasks.append(
                download_gcs_upload_genai(img_url, 
                                          mime_type=mime_type, 
                                          name=name, 
                                          display_url=display_url, 
                                          display_name=display_name)
                                          )

    # Run all tasks in parallel
    if tasks:
        task_content = await asyncio.gather(*tasks)
        content.extend(task_content)

    return content

# Helper function to handle each file download with error handling
async def download_file_with_error_handling(img_url, mime_type, name):
    try:
        return await download_gcs_upload_genai(img_url, mime_type, name)
    except Exception as err:
        msg= f"Error processing file from {img_url}: {str(err)}"
        log.error(msg)
        return {"role": "user", "parts": [{"text": msg}]}

async def download_gcs_upload_genai(img_url, 
                                    mime_type, 
                                    name=None, 
                                    display_url=None, 
                                    display_name=None, 
                                    retries=3, delay=2):
    import aiofiles
    from google.generativeai.types import file_types
    """
    Downloads and uploads a file with retries in case of failure.
    
    Args:
      - img_url: str The URL of the file to download.
      - mime_type: str The MIME type of the file.
      - name: str Optional name, else a random one will be created
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
                msg =  f"The file for {img_url} is too large ({file_size} bytes) to be used directly.  Use RAG instead or {display_url=}"
                return {"role": "user", "parts": [{"text": msg}]}
            
            extension = mimetypes.guess_extension(mime_type)
            
            # Use aiofiles for asynchronous file operations
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
            downloaded_file = temp_file.name

            sanitized_file = sanitize_file(downloaded_file)

            log.info(f"Writing file {sanitized_file}")
            async with aiofiles.open(sanitized_file, 'wb') as f:
                await f.write(file_bytes)

            # Upload the file and get its content reference
            try:
                downloaded_content: file_types.File = await asyncio.to_thread(
                    partial(genai.upload_file, name=name, mime_type=mime_type, display_name=display_name), 
                    sanitized_file
                    )
                return {"role": "user", "parts": [{"file_data": downloaded_content}, 
                                                  {"text": f"You have been given the ability to read and work with filename '{display_name=}' with {mime_type=} {display_url=}"}
                                                  ]}
            except Exception as err:
                msg = f"Could not upload {sanitized_file} to genai.upload_file: {str(err)} {traceback.format_exc()} {display_url=}"
                log.error(msg)
                return {"role": "user", "parts": [{"text": msg}]}
        
        except Exception as err:
            log.error(f"Error processing file {img_url} {mime_type=} on attempt {attempt + 1}/{retries}: {str(err)}")

            if attempt < retries - 1:
                log.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                raise err  # Raise the error after max retries

