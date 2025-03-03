from ..custom_logging import log
from ..gcs import get_bytes_from_gcs

from functools import partial
import mimetypes
import uuid
import asyncio
import tempfile
import re
import os
import traceback
try:
    import google.generativeai as genai
    from google import genai as genaiv2

except ImportError:
    genai = None
    genaiv2 = None

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

async def construct_file_content(gs_list, bucket:str, genai_lib=False):
    """
    Thread-safe implementation for processing multiple files concurrently.
    
    Args:
    - gs_list: a list of dicts representing files in a bucket
    - bucket: The bucket the files are in
    - genai_lib: whether its using the genai SDK
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
        # Generate a unique name for each file to avoid conflicts
        original_name = sanitize_file(file_info['name'])
        unique_name = f"{original_name}_{str(uuid.uuid4())[:8]}"
        display_name = file_info['name']
        log.info(f"Processing {unique_name=} {display_name=}")
        
        try:
            if not genai_lib:
                myfile = genai.get_file(unique_name)
            else:
                client = genaiv2.Client()
                myfile = client.files.get(name=unique_name)
            content.append(myfile)
            content.append(f"You have been given the ability to work with file {display_name=} with {mime_type=} {display_url=}")
            log.info(f"Found existing genai.get_file {unique_name=}")
        except Exception as e:
            log.info(f"Not found checking genai.get_file: '{unique_name}' {str(e)}")
            tasks.append(
                download_gcs_upload_genai(img_url, 
                                         mime_type=mime_type, 
                                         name=unique_name, 
                                         display_url=display_url, 
                                         display_name=display_name,
                                         genai_lib=genai_lib)
                                        )

    # Process files in batches to avoid overwhelming the system
    content_results = []
    batch_size = 3  # Process 3 files at a time
    
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i+batch_size]
        batch_results = await asyncio.gather(*batch)
        content_results.extend(batch_results)
    
    content.extend(content_results)
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
                                    retries=3, delay=2, genai_lib=False):
    """
    Downloads and uploads a file with retries in case of failure.
    Thread-safe implementation using unique file paths.
    
    Args:
      - img_url: str The URL of the file to download.
      - mime_type: str The MIME type of the file.
      - name: str Optional name, else a random one will be created
      - retries: int Number of retry attempts before failing.
      - delay: int Initial delay between retries, exponentially increasing.
      
    Returns:
      - downloaded_content: The result of the file upload if successful.
    """
    import aiofiles
    for attempt in range(retries):
        try:
            log.info(f"Upload attempt [{attempt}] for {img_url=}")
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
                msg = f"The file for {img_url} is too large ({file_size} bytes) to be used directly. Use RAG instead or {display_url=}"
                return {"role": "user", "parts": [{"text": msg}]}
            
            extension = mimetypes.guess_extension(mime_type)
            
            # Create a unique directory for this upload task
            unique_id = str(uuid.uuid4())
            temp_dir = os.path.join(tempfile.gettempdir(), f"upload_{unique_id}")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Create a file with unique path
            file_path = os.path.join(temp_dir, f"file_{unique_id}{extension}")
            
            log.info(f"Writing file {file_path}")
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_bytes)

            try:
                if not genai_lib:
                    downloaded_content = await asyncio.to_thread(
                        partial(genai.upload_file, name=name, mime_type=mime_type, display_name=display_name), 
                        file_path
                    )
                    
                    # Clean up after successful upload
                    try:
                        os.remove(file_path)
                        os.rmdir(temp_dir)
                    except OSError as e:
                        log.warning(f"Cleanup error (non-critical): {str(e)}")
                        
                    return {"role": "user", "parts": [{"file_data": downloaded_content}, 
                                                    {"text": f"You have been given the ability to read and work with filename '{display_name}' with {mime_type=} {display_url=}"}
                                                   ]}
                else:
                    client = genaiv2.Client()
                    
                    # Use semaphore to limit concurrent uploads
                    async with upload_semaphore:
                        downloaded_content = await asyncio.to_thread(
                            client.files.upload, 
                            file=file_path,  
                            config=dict(mime_type=mime_type, display_name=display_name)
                        )
                    
                    # Clean up after successful upload
                    try:
                        os.remove(file_path)
                        os.rmdir(temp_dir)
                    except OSError as e:
                        log.warning(f"Cleanup error (non-critical): {str(e)}")
                        
                    return [downloaded_content, 
                            f"You have been given the ability to read and work with filename '{display_name}' with {mime_type=} {display_url=}"]

            except Exception as err:
                # Clean up on error
                try:
                    os.remove(file_path)
                    os.rmdir(temp_dir)
                except OSError:
                    pass
                
                msg = f"Could not upload {file_path} to {'genai.upload_file' if not genai_lib else 'genaiv2.client.files.upload'}: {str(err)} {traceback.format_exc()} {display_url=}"
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

# Add this at the module level
# Create a semaphore to limit concurrent uploads
upload_semaphore = asyncio.Semaphore(5)  # Adjust the value based on your needs

